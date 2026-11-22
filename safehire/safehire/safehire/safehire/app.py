import os
import re
import sqlite3
from datetime import datetime, timezone

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1_000_000

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "reports.db")


def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                organization TEXT NOT NULL DEFAULT '',
                details TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)


RULES = [
    (25, "An upfront job, registration, training, or security fee is mentioned.",
     r"registration fee|training fee|security fee|interview fee|advance fee|processing fee|joining fee|नौकरी के लिए पैसे|पहले पैसे|ਰਜਿਸਟ੍ਰੇਸ਼ਨ ਫੀਸ"),
    (30, "It asks for an OTP, UPI PIN, password, or banking secret. Never share these.",
     r"upi pin|\botp\b|one.time password|password|card pin|cvv|ओटीपी|पासवर्ड|ਓਟੀਪੀ"),
    (17, "It asks you to move the conversation to WhatsApp, Telegram, or personal contact.",
     r"whats ?app|telegram|personal email|call me|contact me on|व्हाट्सऐप|टेलीग्राम|ਵਟਸਐਪ"),
    (14, "Urgent wording appears. Pause and verify before acting.",
     r"urgent|immediately|act now|today only|limited time|last chance|तुरंत|जल्दी|आज ही|ਜਲਦੀ"),
    (18, "A shortened or unfamiliar link appears. Check it before opening.",
     r"bit\.ly|tinyurl\.com|t\.me/|wa\.me/|click here|open this link|verify your account"),
    (18, "It promises unusually high or guaranteed pay.",
     r"guaranteed job|earn.{0,20}(daily|per day)|instant job|100% selection|घर बैठे.{0,20}कमाई"),
    (18, "It asks you to pay money to receive a payment or refund.",
     r"pay to receive|refund.{0,20}(fee|upi)|पैसे पाने के लिए.{0,15}(फीस|पिन)"),
]


@app.get("/")
def home():
    return render_template("index.html")


@app.post("/api/analyze")
def analyze():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "")

    if not isinstance(message, str) or not message.strip():
        return jsonify({"error": "Paste a message first."}), 400

    if len(message) > 5000:
        return jsonify({"error": "Message must be 5,000 characters or fewer."}), 400

    reasons = []
    score = 0

    for points, reason, pattern in RULES:
        if re.search(pattern, message, flags=re.IGNORECASE):
            score += points
            reasons.append(reason)

    if len(reasons) > 1:
        score += (len(reasons) - 1) * 5

    score = min(score, 100)

    if score >= 60:
        title = "Several risk signals"
    elif score >= 30:
        title = "Review carefully"
    else:
        title = "Few signals found"

    if not reasons:
        reasons.append(
            "No listed warning phrase matched. This does not prove the message is safe."
        )

    return jsonify({
        "score": score,
        "title": title,
        "reasons": reasons,
    })


@app.post("/api/reports")
def create_report():
    data = request.get_json(silent=True) or {}
    organization = data.get("organization", "")
    details = data.get("details", "")

    if not isinstance(organization, str) or not isinstance(details, str):
        return jsonify({"error": "Invalid report."}), 400

    organization = organization.strip()[:80]
    details = details.strip()[:1000]

    if not details:
        return jsonify({"error": "Describe what happened."}), 400

    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    with get_db() as db:
        db.execute(
            """INSERT INTO reports (organization, details, created_at)
               VALUES (?, ?, ?)""",
            (organization, details, created_at),
        )

    return jsonify({"message": "Report saved to the database."}), 201


@app.get("/api/reports")
def list_reports():
    with get_db() as db:
        rows = db.execute("""
            SELECT id, organization, details, created_at
            FROM reports
            ORDER BY id DESC
            LIMIT 50
        """).fetchall()

    return jsonify([dict(row) for row in rows])


@app.errorhandler(413)
def too_large(_error):
    return jsonify({"error": "Request is too large."}), 413


initialize_database()

if __name__ == "__main__":
    app.run(debug=True)
