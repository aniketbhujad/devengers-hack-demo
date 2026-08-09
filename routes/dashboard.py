"""Dashboard blueprint."""

from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import Roadmap, ChatMessage, InterviewSession

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def home():
    recent_roadmaps = (
        Roadmap.query.filter_by(user_id=current_user.id)
        .order_by(Roadmap.created_at.desc())
        .limit(3)
        .all()
    )
    total_roadmaps = Roadmap.query.filter_by(user_id=current_user.id).count()
    total_chats = (
        ChatMessage.query.filter_by(user_id=current_user.id, role="user").count()
    )
    total_interviews = InterviewSession.query.filter_by(user_id=current_user.id).count()

    return render_template(
        "dashboard.html",
        recent_roadmaps=recent_roadmaps,
        total_roadmaps=total_roadmaps,
        total_chats=total_chats,
        total_interviews=total_interviews,
    )
