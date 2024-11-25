# audio-pro

## Developement

```bash
conda create --name audio-pro python=3.10

conda activate audio-pro

pip install uv

```



```bash
docker buildx build -f Dockerfile_enh -t audio-enh .

docker run -d --name audio-enh -it -v /run/user/1000/pipewire-0:/run/user/1000/pipewire-0 audio-enh bash audio_enhance.sh 20

```

```bash
docker buildx build -f Dockerfile_vol -t audio-vol .

docker run -it --rm \
-v /run/user/1000/pulse/native:/run/user/1000/pulse/native:rw \
-v /run/user/1000/pulse/cookie:/run/user/1000/pulse/cookie:ro \
-v /run/user/1000/pipewire-0:/run/user/1000/pipewire-0 \
-p 5002:5002 \
audio-vol bash

```

```bash
docker buildx build -f Dockerfile_ctl -t audio-ctl .
```