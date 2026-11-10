
import os
import hmac
from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Flask, jsonify, request

app = Flask(__name__)

SLOTS = [
    ("combo", "combo1.mp4"),
    ("deste", "deste.mp4"),
    ("combo", "combo2.mp4"),
    ("deste", "deste.mp4"),
]

@app.get("/")
def home():
    return jsonify({
        "project": "X AutoPilot",
        "status": "ready",
        "mode": "dry-run" if os.getenv(
            "DRY_RUN", "true"
        ).lower() != "false" else "live"
    })

@app.get("/api/cron")
def cron():
    secret = os.getenv("CRON_SECRET", "")

    if not secret or not hmac.compare_digest(
        request.headers.get("Authorization", ""),
        f"Bearer {secret}"
    ):
        return jsonify({"error": "Unauthorized"}), 401

    now = datetime.now(ZoneInfo("Europe/Istanbul"))

    slot_index = (
        (now.hour * 2 + now.minute // 30) - 36
    ) % len(SLOTS)

    app_name, video = SLOTS[slot_index]

    if os.getenv("DRY_RUN", "true").lower() != "false":
        return jsonify({
            "status": "dry-run",
            "time": now.isoformat(),
            "app": app_name,
            "video": video,
            "published": False
        })

    return jsonify({
        "status": "not_implemented",
        "message": "X publishing is not connected yet",
        "published": False
    }), 501
