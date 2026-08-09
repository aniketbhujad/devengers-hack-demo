"""Roadmap blueprint – generate and view personalised learning roadmaps."""

import logging
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from extensions import db
from models import Roadmap
from ai_engine import call_granite

logger = logging.getLogger(__name__)
roadmap_bp = Blueprint("roadmap", __name__, url_prefix="/roadmap")


@roadmap_bp.route("/")
@login_required
def index():
    return render_template("roadmap.html")


@roadmap_bp.route("/generate", methods=["POST"])
@login_required
def generate():
    data = request.get_json(force=True)
    career_goal = data.get("career_goal", "").strip()
    current_skills = data.get("current_skills", "").strip()
    study_hours = int(data.get("study_hours_per_week", 10))
    experience_level = data.get("experience_level", "beginner").strip()
    extra_context = data.get("extra_context", "").strip()

    if not career_goal:
        return jsonify({"error": "Career goal is required."}), 400

    prompt = (
        f"Generate a detailed, personalised learning roadmap for the following learner:\n\n"
        f"**Career Goal:** {career_goal}\n"
        f"**Current Skills/Background:** {current_skills or 'None specified'}\n"
        f"**Experience Level:** {experience_level}\n"
        f"**Available Study Time:** {study_hours} hours/week\n"
        f"{'**Extra Context:** ' + extra_context if extra_context else ''}\n\n"
        f"Create a comprehensive, phased roadmap tailored to this learner's profile."
    )

    ai_response = call_granite(
        user_message=prompt,
        extra_system_context=f"The user wants to become a {career_goal}.",
        max_tokens=1800,
        temperature=0.6,
    )

    # Persist to DB
    title = f"Roadmap: {career_goal[:80]}"
    roadmap = Roadmap(
        user_id=current_user.id,
        title=title,
        career_goal=career_goal,
        current_skills=current_skills,
        study_hours_per_week=study_hours,
        experience_level=experience_level,
        content=ai_response,
    )
    db.session.add(roadmap)
    db.session.commit()

    return jsonify({"roadmap": ai_response, "id": roadmap.id, "title": title})


@roadmap_bp.route("/<int:roadmap_id>")
@login_required
def view(roadmap_id):
    roadmap = Roadmap.query.filter_by(id=roadmap_id, user_id=current_user.id).first_or_404()
    return render_template("roadmap_view.html", roadmap=roadmap)


@roadmap_bp.route("/<int:roadmap_id>/delete", methods=["POST"])
@login_required
def delete(roadmap_id):
    roadmap = Roadmap.query.filter_by(id=roadmap_id, user_id=current_user.id).first_or_404()
    db.session.delete(roadmap)
    db.session.commit()
    return jsonify({"success": True})
