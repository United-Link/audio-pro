import sounddevice as sd
import numpy as np

DEVICE_NAME = "DeepFilter Noise Canceling Source"
# DEVICE_NAME = "US-2x2HR"

# 設定音訊參數
SAMPLE_RATE = 48000  # 取樣率
DURATION = 0.16  # 每次擷取的音訊長度 (秒)
BLOCKSIZE = int(SAMPLE_RATE * DURATION)  # 每次讀取的樣本數

# 找到 TASCAM US-2x2 HR 的輸出裝置索引
device_info = sd.query_devices()
print(device_info)

device_index = None
for dev in device_info:
    if DEVICE_NAME in dev["name"] and dev["max_output_channels"] > 0:
        device_index = dev["index"]

if device_index is None:
    print("找不到 TASCAM US-2x2 HR 輸出裝置")
    exit()


# 定義一個全域變數來儲存音訊資料
audio_data = None


# 定義音訊串流的回呼函數
def callback(indata, frames, time, status):
    global audio_data
    if status:
        print(status)
    audio_data = indata.copy()  # 將音訊資料複製到全域變數


# 開啟音訊串流
try:
    with sd.InputStream(
        device=device_index,
        channels=3,  # 單聲道
        samplerate=SAMPLE_RATE,
        callback=callback,
        blocksize=BLOCKSIZE,  # 每次擷取的樣本數
        dtype=np.float32,
    ) as stream:
        print("開始擷取音訊...")
        while True:
            # 等待音訊資料被回呼函數更新
            if audio_data is not None:
                vol_max = np.max(audio_data, axis=0)
                dbfs_max = np.maximum(20 * np.log10(vol_max), -120)
                print(dbfs_max)
                # 檢查形狀並處理
                # if audio_data.shape == (BLOCKSIZE, 1):
                #     print(audio_data[:, 0])  # 二維陣列 (n, 1)
                # elif audio_data.shape == (BLOCKSIZE,):
                #     # print(audio_data)  # 一維陣列 (n,)
                #     vol_max = np.max(audio_data, axis=0)
                #     dbfs_max = np.maximum(20 * np.log10(vol_max), -120)
                #     print(dbfs_max)
                # else:
                #     print("音訊資料形狀錯誤:", audio_data.shape)
                audio_data = None  # 清空音訊資料，等待下一次更新
            sd.sleep(int(DURATION * 1000))  # 等待一段時間，避免 CPU 使用率過高

except KeyboardInterrupt:
    print("停止擷取音訊...")

except sd.PortAudioError as e:
    print(f"PortAudio 錯誤: {e}")
    print("請檢查您的音訊設備是否已正確連接和配置。")
