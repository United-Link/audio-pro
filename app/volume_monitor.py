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

# results = {
#     "max_dbfs": {"input": "-inf", "output": "-inf"},
#     "rms_dbfs": {"input": "-inf", "output": "-inf"},
#     "status": "running",
# }

results_old = {"input_dbfs": "-inf", "output_dbfs": "-inf"}


def get_device_index(device_info, device_name):
    for device in device_info:
        if device_name in device["name"] and device["max_output_channels"] > 0:
            device_index = device["index"]
            return device_index
    else:
        return None


# 定義音訊串流的回呼函數
def callback(indata, frames, time, status):
    global audio_data
    if status:
        print(status)
    audio_data = indata.copy()  # 將音訊資料複製到全域變數


# def inputstream_recorder(queue, device):
#     def callback(indata, frames, time, status):
#         if status:
#             print(status)
#         if not queue.full():
#             try:
#                 queue.put(indata, block=False)
#             except queue.Full:
#                 print("Queue (inputstream) is full.")

#     with sd.InputStream(
#         samplerate=FS,
#         channels=CHANNELS,
#         device=device,
#         blocksize=REC_SAMPLES,
#         callback=callback,
#     ):
#         while True:
#             time.sleep(SLEEP_DURATION)


# def compute_dbfs(queue):
#     global results
#     global results_old

#     while True:
#         if not queue.empty():
#             data = queue.get()

#             vol_max = np.max(data[:, [0, 2]], axis=0)
#             dbfs_max = np.maximum(20 * np.log10(vol_max), -120)

#             # vol_rms = np.sqrt(np.mean(data[:, [0, 2]] ** 2, axis=0))
#             # dbfs_rms = max(20 * np.log10(vol_rms), -120)

#             # results["max_dbfs"] = {
#             #     "input": f"{dbfs_max[0]:.2f}",
#             #     "output": f"{dbfs_max[1]:.2f}",
#             # }
#             # results["rms_dbfs"] = {
#             #     "input": f"{dbfs_rms[0]:.2f}",
#             #     "output": f"{dbfs_rms[1]:.2f}",
#             # }
#             results_old["input_dbfs"] = f"{dbfs_max[0]:.2f}"
#             results_old["output_dbfs"] = f"{dbfs_max[1]:.2f}"

#         time.sleep(SLEEP_DURATION)


device_info = sd.query_devices()
device_index = get_device_index(device_info, DEVICE_NAME)
if device_index is None:
    raise Exception(f"'{DEVICE_NAME}' is not found.")

audio_data = None

with sd.InputStream(
    device=device_index,
    channels=4,  # 單聲道
    samplerate=SAMPLE_RATE,
    callback=callback,
    blocksize=BLOCKSIZE,  # 每次擷取的樣本數
    dtype=np.float32,
) as stream:
    print("開始擷取音訊...")
    while True:
        # 等待音訊資料被回呼函數更新
        if audio_data is not None:
            vol_max = np.max(audio_data[:, [2, 0]], axis=0)
            dbfs_max = np.maximum(20 * np.log10(vol_max), -120)

            results_old["input_dbfs"] = f"{dbfs_max[0]:.2f}"
            results_old["output_dbfs"] = f"{dbfs_max[1]:.2f}"

            audio_data = None  # 清空音訊資料，等待下一次更新
        time.sleep(DURATION / 2)  # 等待一段時間，避免 CPU 使用率過高


# queue_dfn = queue.Queue(maxsize=1)

# audio_process = Thread(target=inputstream_recorder, args=(queue_dfn, device_index))
# audio_process.start()

# dbfs_process = Thread(target=compute_dbfs, args=(queue_dfn,))
# dbfs_process.start()


@app.route("/vol_monitor")
def vol_monitor():
    # return jsonify(results)
    return jsonify(results_old)


if __name__ == "__main__":
    server = pywsgi.WSGIServer(("0.0.0.0", 5002), app)
    server.serve_forever()
