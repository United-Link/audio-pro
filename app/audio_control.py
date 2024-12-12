"""
Author: Hung-Shin Lee
Copyright 2024 United Link Co., Ltd.
"""

import os
import re
import json
import subprocess

from gevent import pywsgi
from flask_cors import CORS
from flask import Flask, request, jsonify

app = Flask(__name__)
CORS(app)


COMPOSE_FILE = "docker-compose_services.yml"
DEFAULT_LIMIT = 20


def check_device_exists():
    try:
        result = subprocess.run(["lsusb"], capture_output=True, text=True, check=True)
        return "US-2x2HR" in result.stdout
    except subprocess.CalledProcessError:
        return False


def query_default_audio_devices():
    default_source = None
    default_sink = None

    try:
        result = subprocess.run(
            ["pactl", "info"], capture_output=True, text=True, check=True
        )
        output = result.stdout
        match = re.search(r"Default Source:\s*(.+)", output)
        default_source = match.group(1) if match else None

        match = re.search(r"Default Sink:\s*(.+)", output)
        default_sink = match.group(1) if match else None

        return default_source, default_sink
    except (
        subprocess.CalledProcessError,
        AttributeError,
    ):
        return default_source, default_sink


def set_volume_levels(device, kind: str):
    if kind == "source":
        commmand = "set-source-volume"
    elif kind == "sink":
        commmand = "set-sink-volume"
    else:
        return False

    try:
        subprocess.run(
            ["pactl", commmand, device, "100%"],
            capture_output=True,
            text=True,
            check=True,
        )
        return True

    except subprocess.CalledProcessError as e:
        print(e.stderr)
        return False


def check_audio_vol():
    try:
        result = subprocess.run(
            ["docker", "inspect", "--format={{json .State}}", "audio-vol"],
            capture_output=True,
            text=True,
            check=True,
        )
        state_json = result.stdout.strip()
        if state_json:
            state_dict = json.loads(state_json)
            if state_dict["Running"]:
                return True
            else:
                return False
        else:
            return False
    except subprocess.CalledProcessError:
        return False
    except json.JSONDecodeError:
        return False
    except Exception:
        return False


def check_audio_enh():
    try:
        result = subprocess.run(
            ["docker", "inspect", "--format={{json .State}}", "audio-enh"],
            capture_output=True,
            text=True,
            check=True,
        )
        state_json = result.stdout.strip()
        if state_json:
            state_dict = json.loads(state_json)
            if state_dict["Running"]:
                result = subprocess.run(
                    ["docker", "inspect", "--format={{.Config.Cmd}}", "audio-enh"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                command = result.stdout.strip()
                match = re.search(r"\[bash audio_enhance.sh (\d+)\]", command)
                if match:
                    limit = int(match.group(1))
                    return True, limit
                else:
                    raise Exception(f"Invalid Command: {command}")
            else:
                raise Exception("Not Running")
        else:
            raise Exception("No State")
    except subprocess.CalledProcessError:
        print("CalledProcessError")
        return False, None
    except json.JSONDecodeError:
        print("JSONDecodeError")
        return False, None
    except Exception as e:
        print(e)
        return False, None


def _get_audio_status():
    status = {
        "device": False,
        "source": False,
        "sink": False,
        "audio-vol": False,
        "audio-enh": False,
        "limit": None,
    }

    pre_flag = True
    if check_device_exists():
        status["device"] = True
        default_source, default_sink = query_default_audio_devices()
        if default_source is not None:
            if set_volume_levels(default_source, "source"):
                status["source"] = True
            else:
                pre_flag = False
        else:
            pre_flag = False

        if default_sink is not None:
            if set_volume_levels(default_sink, "sink"):
                status["sink"] = True
            else:
                pre_flag = False
        else:
            pre_flag = False
    else:
        pre_flag = False

    if pre_flag:
        audio_vol_status = check_audio_vol()
        if audio_vol_status:
            status["audio-vol"] = True

        audio_enh_status, limit = check_audio_enh()
        if audio_enh_status:
            status["audio-enh"] = True
            status["limit"] = limit

    return status


@app.route("/audio_status", methods=["GET"])
def get_audio_status():
    status = _get_audio_status()

    return jsonify(status)


@app.route("/restart_services", methods=["PUT"])
def restart_services():
    data = request.get_json(silent=True)
    if not data:
        limit = DEFAULT_LIMIT
    else:
        limit = data.get("limit", DEFAULT_LIMIT)

    if not isinstance(limit, int):
        response_data = {
            "status": "error",
            "message": "Invalid limit value, must be a non-negative integer",
        }
        return jsonify(response_data), 400

    if int(limit) < 0 or int(limit) > 100:
        response_data = {
            "status": "error",
            "message": "Limit must be between 0 and 100",
        }
        return jsonify(response_data), 400

    status = _get_audio_status()
    if status["audio-enh"]:
        if not os.path.exists(COMPOSE_FILE):
            response_data = {
                "status": "error",
                "message": "Compose File not found",
            }
            return jsonify(response_data), 400

        # subprocess.run(
        #     [
        #         "docker",
        #         "compose",
        #         "-f",
        #         COMPOSE_FILE,
        #         "down",
        #     ],
        #     check=True,
        #     capture_output=True,
        # )

        subprocess.run(
            ["docker", "rm", "-f", "audio-vol"],
            check=True,
            capture_output=True,
            text=True,
        )

        subprocess.run(
            ["docker", "rm", "-f", "audio-enh"],
            check=True,
            capture_output=True,
            text=True,
        )

        subprocess.run(
            [
                "docker",
                "compose",
                "-f",
                COMPOSE_FILE,
                "up",
                "-d",
            ],
            check=True,
            capture_output=True,
            text=True,
            env={**os.environ, "LIMIT": str(limit)},
        )

        response_data = {
            "status": "success",
            "message": f"Limit set to {limit}",
        }
        return jsonify(response_data), 200
    else:
        response_data = {
            "status": "error",
            "message": "audio-enh is not running",
        }
        return jsonify(response_data), 400


if __name__ == "__main__":
    server = pywsgi.WSGIServer(("0.0.0.0", 5003), app)
    server.serve_forever()
