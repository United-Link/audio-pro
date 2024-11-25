# audio-pro

## Developement

```bash
conda create --name audio-pro python=3.10

conda activate audio-pro

pip install uv

```

```bash
docker buildx build -f Dockerfile_enh -t audio-enh .

docker run --rm --name audio-enh -it -v /run/user/1000/pipewire-0:/run/user/1000/pipewire-0 -e XDG_RUNTIME_DIR=/run/user/1000 audio-enh bash

```
