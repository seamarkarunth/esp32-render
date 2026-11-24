import os
import secrets
import time

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1024

device = {
    "led": "UNKNOWN",
    "uptime": 0,
    "last_seen": 0
}


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.get("/api/status")
def device_status():
    online = time.time() - device["last_seen"] < 20

    return jsonify(
        device="ESP32",
        connected=online,
        led=device["led"] if online else "UNKNOWN",
        uptime=device["uptime"],
        message=(
            "Receiving ESP32 reports"
            if online
            else "Waiting for ESP32 connection"
        )
    )


@app.post("/api/device/status")
def receive_status():
    expected_key = os.environ.get("DEVICE_KEY", "")

    if not expected_key:
        return jsonify(error="Server device key is not configured"), 503

    supplied_key = request.headers.get("X-Device-Key", "")

    if not secrets.compare_digest(
        supplied_key.encode(), expected_key.encode()
    ):
        return jsonify(error="Unauthorized"), 401

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify(error="Expected a JSON object"), 400

    if data.get("led") not in ("ON", "OFF", "BLINK"):
        return jsonify(error="LED must be ON, OFF or BLINK"), 400

    uptime = data.get("uptime")

    if type(uptime) is not int or uptime < 0:
        return jsonify(error="Uptime must be a non-negative integer"), 400

    device.update(
        led=data["led"],
        uptime=uptime,
        last_seen=time.time()
    )

    return jsonify(status="accepted")
