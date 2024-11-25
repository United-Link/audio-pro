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

docker run -d --name audio-vol -it \
-v /run/user/1000/pulse/native:/run/user/1000/pulse/native:rw \
-v /run/user/1000/pulse/cookie:/run/user/1000/pulse/cookie:ro \
-v /run/user/1000/pipewire-0:/run/user/1000/pipewire-0 \
-p 5002:5002 \
audio-vol python volume_monitor.py

```
```bash
docker compose -f ~/audio-pro/docker-compose_services.yml up -d
docker compose -f ~/audio-pro/docker-compose_services.yml down

docker compose -f ~/audio-pro/docker-compose_control.yml up -d
docker compose -f ~/audio-pro/docker-compose_control.yml down

```

```bash
docker buildx build -f Dockerfile_ctl -t audio-ctl .

docker run --name audio-ctl --rm -it \
--device /dev/bus/usb:/dev/bus/usb \
-v /run/user/$(id -u)/pulse:/run/user/$(id -u)/pulse \
-e PULSE_SERVER=unix:/run/user/$(id -u)/pulse/native \
-v /var/run/docker.sock:/var/run/docker.sock \
-v /mnt/audio-pro/docker-comose_services.yaml:/usr/src/app/docker-comose_services.yaml \
-p 5003:5003 \
audio-ctl bash


docker run -d --name audio-ctl -it \
--device /dev/bus/usb:/dev/bus/usb \
-v /run/user/$(id -u)/pulse:/run/user/$(id -u)/pulse \
-e PULSE_SERVER=unix:/run/user/$(id -u)/pulse/native \
-v /var/run/docker.sock:/var/run/docker.sock \
-v /mnt/audio-pro/docker-comose_services.yaml:/usr/src/app/docker-comose_services.yaml \
-p 5003:5003 \
audio-ctl python audio_control.py
```