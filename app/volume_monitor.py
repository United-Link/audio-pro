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
SAMPLE_RATE = 48000
CHANNELS = 3
BLOCKSIZE = int(DURATION * SAMPLE_RATE)

results = {"input_dbfs": "-inf", "output_dbfs": "-inf"}


def get_device_index(device_info, device_name):
    for device in device_info:
        if device_name in device["name"] and device["max_output_channels"] > 0:
            device_index = device["index"]
            return device_index
    else:
        return None


def inputstream(audio_data: queue.Queue, device_index: int):
    def callback(indata, frames, time, status):
        if status:
            print(status)

        if not audio_data.full():
            audio_data.put(indata, block=False)

    with sd.InputStream(
        device=device_index,
        channels=CHANNELS,
        samplerate=SAMPLE_RATE,
        callback=callback,
        blocksize=BLOCKSIZE,
    ):
        while True:
            time.sleep(DURATION / 2)


def compute_dbfs(audio_data: queue.Queue):
    global results

    while True:
        if not audio_data.empty():
            data = audio_data.get()

            vol_max = np.max(data[:, [2, 0]], axis=0)
            dbfs_max = np.maximum(20 * np.log10(vol_max), -120)

            # vol_rms = np.sqrt(np.mean(data[:, [2, 0]] ** 2, axis=0))
            # dbfs_rms = np.maximum(20 * np.log10(vol_rms), -120)

            results["input_dbfs"] = f"{dbfs_max[0]:.2f}"
            results["output_dbfs"] = f"{dbfs_max[1]:.2f}"

        time.sleep(DURATION / 2)


device_info = sd.query_devices()
device_index = get_device_index(device_info, DEVICE_NAME)
if device_index is None:
    raise Exception(f"'{DEVICE_NAME}' is not found.")

audio_data = queue.Queue(maxsize=1)

audio_process = Thread(target=inputstream, args=(audio_data, device_index))
audio_process.start()

dbfs_process = Thread(target=compute_dbfs, args=(audio_data,))
dbfs_process.start()


@app.route("/vol_monitor")
def vol_monitor():
    return jsonify(results)


if __name__ == "__main__":
    server = pywsgi.WSGIServer(("0.0.0.0", 5002), app)
    server.serve_forever()
