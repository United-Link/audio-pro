"""
Author: Hung-Shin Lee
Copyright 2024 United Link Co., Ltd.
"""

import time
import queue
from threading import Thread

import numpy as np
import sounddevice as sd
from gevent import pywsgi
from flask_cors import CORS
from flask import Flask, jsonify


app = Flask(__name__)
CORS(app)

DEVICE_NAME = "DeepFilter Noise Canceling Source"

DURATION = 0.16
SLEEP_DURATION = 0.08
FS = 48000
CHANNELS = 3
REC_SAMPLES = int(DURATION * FS)

results = {
    "max": {"input_dbfs": "-inf", "output_dbfs": "-inf"},
    "rms": {"input_dbfs": "-inf", "output_dbfs": "-inf"},
    "status": "running",
}


@app.route("/vol_monitor")
def vol_monitor():
    return jsonify(results)


def get_device_index_by_name(devices, device_name):
    for index, device in enumerate(devices):
        if device_name in device["name"]:
            return index

    return None


def inputstream_recorder(queue, device):
    def callback(indata, frames, time, status):
        if status:
            print(status)
        if not queue.full():
            try:
                queue.put(indata, block=False)
            except queue.Full:
                print("Queue (inputstream) is full.")

    with sd.InputStream(
        samplerate=FS,
        channels=CHANNELS,
        device=device,
        blocksize=REC_SAMPLES,
        callback=callback,
    ):
        while True:
            time.sleep(SLEEP_DURATION)


def sdrec_recorder(queue, device):
    while True:
        recording = sd.rec(REC_SAMPLES, samplerate=FS, channels=CHANNELS, device=device)
        sd.wait()

        if not queue.full():
            try:
                queue.put(recording, block=False)
            except queue.Full:
                print("Queue (sdrec) is full.")


def compute_dbfs(queue):
    global results

    while True:
        if not queue.empty():
            data = queue.get()

            vol_max = np.max(data[:, [0, 2]], axis=0)
            dbfs_max = 20 * np.log10(vol_max)

            vol_rms = np.sqrt(np.mean(data[:, [0, 2]] ** 2, axis=0))
            dbfs_rms = 20 * np.log10(vol_rms)

            results["max"] = {
                "input_dbfs": f"{dbfs_max[0]:.2f}",
                "output_dbfs": f"{dbfs_max[1]:.2f}",
            }
            results["rms"] = {
                "input_dbfs": f"{dbfs_rms[0]:.2f}",
                "output_dbfs": f"{dbfs_rms[1]:.2f}",
            }

        time.sleep(SLEEP_DURATION)


devices = sd.query_devices()
try:
    device_index = get_device_index_by_name(devices, DEVICE_NAME)
    if device_index is None:
        raise ValueError(f"'{DEVICE_NAME}' is not found.")
except ValueError:
    results["status"] = "error"
    device_index = None

if device_index is not None:
    queue_dfn = queue.Queue(maxsize=1)

    audio_process = Thread(target=inputstream_recorder, args=(queue_dfn, device_index))
    audio_process.start()

    dbfs_process = Thread(target=compute_dbfs, args=(queue_dfn,))
    dbfs_process.start()


if __name__ == "__main__":
    server = pywsgi.WSGIServer(("0.0.0.0", 5002), app)
    server.serve_forever()
