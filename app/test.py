import sounddevice as sd
import numpy as np

# 設定音訊參數
SAMPLE_RATE = 48000  # 取樣率
DURATION = 0.1  # 每次擷取的音訊長度 (秒)

# 找到 TASCAM US-2x2 HR 的輸出裝置索引
device_info = sd.query_devices()
device_index = None
for i, dev in enumerate(device_info):
    if "TASCAM US-2x2 HR" in dev["name"] and dev["max_output_channels"] > 0:
        if "playback_FL" in dev["name"]:
            device_index = i
            break
if device_index is None:
    print("找不到 TASCAM US-2x2 HR 輸出裝置")
    exit()


# 定義音訊串流的回呼函數
def callback(outdata, frames, time, status):
    if status:
        print(status)
    # 在這裡，outdata 是空的，因為我們只讀取，不輸出。
    # 如果需要輸出音訊，可以在這裡填充 outdata。


# 開啟音訊串流
try:
    with sd.InputStream(
        device=device_index,
        channels=1,  # 單聲道
        samplerate=SAMPLE_RATE,
        callback=callback,
        blocksize=int(SAMPLE_RATE * DURATION),  # 每次擷取的樣本數
        dtype=np.float32,
    ) as stream:
        print("開始擷取音訊...")
        while True:
            # 獲取音訊數據
            audio_data = stream.read(int(SAMPLE_RATE * DURATION))[0]

            # 顯示音訊值
            print(audio_data)

except KeyboardInterrupt:
    print("停止擷取音訊...")

except sd.PortAudioError as e:
    print(f"PortAudio 錯誤: {e}")
    print("請檢查您的音訊設備是否已正確連接和配置。")
