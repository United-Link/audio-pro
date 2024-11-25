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
from flask import Flask, request, jsonify, Response


app = Flask(__name__)
CORS(app)

DURATION = 0.16
SLEEP_DURATION = 0.08
FS = 48000
CHANNELS = 3
REC_SAMPLES = int(DURATION * FS)


@app.route("/vol_monitor")
def vol_monitor():
    return jsonify(scores)

@app.route("/metrics", methods=["GET"])
def get_metrics():
    return Response(generate_latest(), mimetype="text/plain")


def get_device_index_by_name(devices, name):
    for index, device in enumerate(devices):
        if name in device["name"]:
            return index
    return None


def inputstream_recorder(queue, device):
    def callback(indata, frames, time, status):
        if status:
            print(status)
        if not queue.full():
            try:
                queue.put(indata.copy(), block=False)
            except:
                pass

    with sd.InputStream(samplerate=FS, channels=CHANNELS, device=device, blocksize=REC_SAMPLES, callback=callback):
        while True:
            time.sleep(SLEEP_DURATION)


def sdrec_recorder(queue, device):
    while True:
        recording = sd.rec(REC_SAMPLES, samplerate=FS, channels=CHANNELS, device=device)
        sd.wait() 
        
        if not queue.full():
            try:
                queue.put(recording.copy(), block=False)
            except:
                pass


def compute_dbfs(queue):
    global scores

    while True:
        if not queue.empty():
            data = queue.get()

            # vol_max = np.max(data[:, [0, 2]], axis=0)
            # dbfs = 20 * np.log10(vol_max)

            vol_rms = np.sqrt(np.mean(data[:, [0, 2]] ** 2, axis=0))
            dbfs = 20 * np.log10(vol_rms)

            input_dbfs_metric.set(dbfs[0])
            output_dbfs_metric.set(dbfs[1])
            scores["input_dbfs"] = f"{dbfs[0]:.2f}"
            scores["output_dbfs"] = f"{dbfs[1]:.2f}"
            
        time.sleep(SLEEP_DURATION)


scores = {"input_dbfs": "", "output_dbfs": ""}

devices = sd.query_devices()

queue_dfn = queue.Queue(maxsize=1)
device_name = "DeepFilter Noise Canceling Source"
device_index = get_device_index_by_name(devices, device_name)
print(f"Device: {device_name} ({device_index})")

audio_process = Thread(target=inputstream_recorder, args=(queue_dfn, device_index))
audio_process.start()

dbfs_process = Thread(target=compute_dbfs, args=(queue_dfn,))
dbfs_process.start()

@app.route("/health")
def check_health():
    if device_index is not None:
        return {}, 200
    else:
        return {}, 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5002)
