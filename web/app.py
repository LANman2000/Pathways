from flask import Flask
from flask import request
from flask import jsonify
from werkzeug.exceptions import HTTPException

from src.pathway_engine import PathwayEngine
from src.formatter import InvalidAnalysisResponse
from src.student_profile import StudentProfile

import hashlib
import os
import sqlite3
import tempfile
import time
from pathlib import Path


app = Flask(__name__)

engine = None

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
AUTH_DB = Path(os.environ.get(
    "PATHWAYS_DB",
    REPOSITORY_ROOT / "apps" / "account-access" / "server" / "data" / "accounts.sqlite"
))
UPLOAD_FOLDER = Path(os.environ.get("PATHWAYS_UPLOAD_FOLDER", REPOSITORY_ROOT / "uploads"))
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024


def authenticated_user():
    raw_token = request.cookies.get("pathways_session")
    if not raw_token or not AUTH_DB.is_file():
        return None

    hashed_token = hashlib.sha256(raw_token.encode()).hexdigest()
    db = sqlite3.connect(AUTH_DB)
    try:
        return db.execute(
            """
            SELECT users.id, users.name, users.email
            FROM sessions
            JOIN users ON users.id = sessions.user_id
            WHERE sessions.token = ? AND sessions.expires > ?
            """,
            (hashed_token, time.time()),
        ).fetchone()
    finally:
        db.close()


def get_engine():
    global engine
    if engine is None:
        engine = PathwayEngine()
    return engine


def save_upload(upload):
    if upload is None or not upload.filename:
        return None
    with tempfile.NamedTemporaryFile(dir=UPLOAD_FOLDER, delete=False) as temporary:
        upload.save(temporary)
        return temporary.name


@app.errorhandler(InvalidAnalysisResponse)
def handle_invalid_analysis_response(_error):
    return jsonify({
        "error": "Analysis provider returned an invalid response."
    }), 502


@app.errorhandler(HTTPException)
def handle_http_error(error):
    return jsonify({"error": error.description}), error.code


@app.errorhandler(Exception)
def handle_unexpected_error(error):
    app.logger.exception("Unhandled API error")
    return jsonify({"error": "Analysis failed. Please try again."}), 500


@app.route("/api/analyze", methods=["POST"])
@app.route("/analyze", methods=["POST"])
def analyze():
    if authenticated_user() is None:
        return jsonify({"error": "Authentication required."}), 401

    major = request.form.get("major", "")

    interests = request.form.get("interests", "")

    goals = request.form.get("goals", "")

    volunteer_experience = request.form.get(
        "volunteer_experience",
        ""
    )

    skills = request.form.getlist("skills")

    certifications = request.form.getlist(
        "certifications"
    )

    profile = StudentProfile(
        major=major,
        interests=interests,
        goals=goals,
        skills=skills,
        volunteer_experience=volunteer_experience,
        certifications=certifications
    )

    transcript_path = None
    resume_path = None
    try:
        transcript_path = save_upload(request.files.get("transcript"))
        resume_path = save_upload(request.files.get("resume"))
        result = get_engine().analyze_student(
            profile,
            transcript_path,
            resume_path
        )
        return jsonify(result)
    finally:
        for path in (transcript_path, resume_path):
            if path:
                Path(path).unlink(missing_ok=True)


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=int(os.environ.get("PATHWAYS_ANALYSIS_PORT", "5000")),
        debug=False,
    )