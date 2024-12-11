# audio-pro

## NOTE
1. volume_monitor.py 仍是舊版
2. GitHub Repo 權限目前是 Public


## Developement Environment

```bash
conda create --name audio-pro python=3.10

conda activate audio-pro

pip install -r requirements.txt

```


## AUDIO ENHANCE

```bash
docker buildx build -f Dockerfile_enh -t audio-enh .

docker run --name audio-enh --rm -it \
-v /run/user/1000/pipewire-0:/run/user/1000/pipewire-0 \
-v /etc/localtime:/etc/localtime:ro \
-v /etc/timezone:/etc/timezone:ro \
-e XDG_RUNTIME_DIR=/run/user/1000 \
audio-enh bash

bash audio_enhance.sh 20
```


## VOLUME MONITOR

```bash
docker buildx build -f Dockerfile_vol -t audio-vol .

docker run --name audio-vol --rm -it \
-v /run/user/1000/pipewire-0:/run/user/1000/pipewire-0 \
-v /run/user/1000/pulse/native:/run/user/1000/pulse/native \
-p 5002:5002 \
audio-vol bash

docker run --name audio-vol --rm -it \
--volume /run/user/$UID/pipewire-0:/run/user/$UID/pipewire-0 \
--env PIPEWIRE_RUNTIME_DIR=/run/user/$UID/pipewire-0 \
--env XDG_RUNTIME_DIR=/run/user/$UID \
audio-vol bash


```
```bash
curl http://10.22.2.151:5002/vol_monitor
```


## AUDIO CONTROL

```bash
docker buildx build -f Dockerfile_ctl -t audio-ctl .

docker run -d --name audio-ctl -it \
--device /dev/bus/usb:/dev/bus/usb \
-v /run/user/1000/pulse:/run/user/1000/pulse \
-e PULSE_SERVER=unix:/run/user/1000/pulse/native \
-v /var/run/docker.sock:/var/run/docker.sock \
-v /mnt/audio/audio-pro/docker-compose_services.yml:/usr/src/app/docker-compose_services.yml \
-p 5003:5003 \
audio-ctl python audio_control.py
```

```bash
curl http://10.22.1.151:5003/audio_status

curl -X PUT http://10.22.1.151:5003/restart_services \
-H "Content-Type: application/json" \
-d '{"limit": 32}'
```


## DOCKER COMPOSE

```bash
LIMIT=20 docker compose -f /mnt/audio/audio-pro/docker-compose_services.yml build
LIMIT=20 docker compose -f /mnt/audio/audio-pro/docker-compose_services.yml up -d
LIMIT=20 docker compose -f /mnt/audio/audio-pro/docker-compose_services.yml down

docker compose -f /mnt/audio/audio-pro/docker-compose_control.yml up -d
docker compose -f /mnt/audio/audio-pro/docker-compose_control.yml down
```