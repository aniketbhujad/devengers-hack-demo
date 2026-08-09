"""Interview blueprint – AI-powered interview preparation."""

import logging
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import InterviewSession
from ai_engine import call_granite

logger = logging.getLogger(__name__)
interview_bp = Blueprint("interview", __name__, url_prefix="/interview")


@interview_bp.route("/")
@login_required
def index():
    return render_template("interview.html")


@interview_bp.route("/generate", methods=["POST"])
@login_required
def generate():
    data = request.get_json(force=True)
    job_role = data.get("job_role", "").strip()
    company_type = data.get("company_type", "tech company").strip()
    experience_level = data.get("experience_level", "junior").strip()
    focus_areas = data.get("focus_areas", "").strip()

    if not job_role:
        return jsonify({"error": "Job role is required."}), 400

    prompt = (
        f"Generate a comprehensive interview preparation plan for:\n\n"
        f"**Job Role:** {job_role}\n"
        f"**Company Type:** {company_type}\n"
        f"**Experience Level:** {experience_level}\n"
        f"**Focus Areas / Tech Stack:** {focus_areas or 'General'}\n\n"
        f"Include:\n"
        f"1. 5 HR/Behavioural questions with STAR-format answer guidance\n"
        f"2. 8-10 technical questions with key answer points\n"
        f"3. Role-specific preparation tips\n"
        f"4. Recommended practice resources\n"
        f"5. A 2-week preparation schedule"
    )

    ai_response = call_granite(
        user_message=prompt,
        extra_system_context=f"The user is preparing for a {experience_level} {job_role} role at a {company_type}.",
        max_tokens=2000,
        temperature=0.65,
    )

    interview = InterviewSession(
        user_id=current_user.id,
        job_role=job_role,
        company_type=company_type,
        experience_level=experience_level,
        focus_areas=focus_areas,
        content=ai_response,
    )
    db.session.add(interview)
    db.session.commit()

    return jsonify({"plan": ai_response, "id": interview.id, "job_role": job_role})


@interview_bp.route("/<int:session_id>/delete", methods=["POST"])
@login_required
def delete(session_id):
    interview = InterviewSession.query.filter_by(
        id=session_id, user_id=current_user.id
    ).first_or_404()
    db.session.delete(interview)
    db.session.commit()
    return jsonify({"success": True})
