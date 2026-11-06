from flask import Flask
from flask import request
from flask import jsonify
from werkzeug.exceptions import HTTPException

from src.pathway_engine import PathwayEngine
from src.formatter import InvalidAnalysisResponse
from src.student_profile import StudentProfile

import os


app = Flask(__name__)

engine = PathwayEngine()

UPLOAD_FOLDER = "uploads"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


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

    transcript = request.files.get("transcript")

    resume = request.files.get("resume")

    if transcript:

        transcript_path = os.path.join(
            UPLOAD_FOLDER,
            transcript.filename
        )

        transcript.save(transcript_path)

    if resume:

        resume_path = os.path.join(
            UPLOAD_FOLDER,
            resume.filename
        )

        resume.save(resume_path)

    result = engine.analyze_student(
        profile,
        transcript_path,
        resume_path
    )

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)