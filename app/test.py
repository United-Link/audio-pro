import pyaudio
import numpy as np

# 設定音訊參數
FORMAT = pyaudio.paFloat32  # 音訊格式
CHANNELS = 1  # 聲道數
RATE = 44100  # 取樣率
CHUNK = 1024  # 每次讀取的音訊幀數

# 找到 TASCAM US-2x2 HR 的輸出裝置索引
p = pyaudio.PyAudio()
device_index = None
for i in range(p.get_device_count()):
    dev = p.get_device_info_by_index(i)
    if "TASCAM US-2x2 HR" in dev["name"] and dev["maxOutputChannels"] > 0:
        if "playback_FL" in dev["name"]:
            device_index = i
            break
if device_index is None:
    print("找不到 TASCAM US-2x2 HR 輸出裝置")
    exit()

# 開啟音訊串流
stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=False,
    output=True,
    output_device_index=device_index,
    frames_per_buffer=CHUNK,
)

print("開始擷取音訊...")

try:
    while True:
        # 讀取音訊資料
        data = stream.read(CHUNK)

        # 將音訊資料轉換為 NumPy 陣列
        audio_data = np.frombuffer(data, dtype=np.float32)

        # 顯示音訊值
        print(audio_data)

except KeyboardInterrupt:
    print("停止擷取音訊...")

finally:
    # 停止並關閉音訊串流
    stream.stop_stream()
    stream.close()
    p.terminate()
