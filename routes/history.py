"""History blueprint – view all past roadmaps, chats, and interview sessions."""

import uuid
from flask import Blueprint, render_template, request, jsonify, session
from flask_login import login_required, current_user
from models import Roadmap, ChatMessage, InterviewSession
from extensions import db

history_bp = Blueprint("history", __name__, url_prefix="/history")


@history_bp.route("/")
@login_required
def index():
    tab = request.args.get("tab", "roadmaps")
    return render_template("history.html", active_tab=tab)


@history_bp.route("/roadmaps")
@login_required
def roadmaps():
    items = (
        Roadmap.query.filter_by(user_id=current_user.id)
        .order_by(Roadmap.created_at.desc())
        .all()
    )
    return jsonify([r.to_dict() for r in items])


@history_bp.route("/chats")
@login_required
def chats():
    """Return distinct chat sessions with their first user message as a title."""
    rows = (
        ChatMessage.query.filter_by(user_id=current_user.id, role="user")
        .order_by(ChatMessage.created_at.desc())
        .all()
    )
    # Group by session_id
    sessions_seen: dict = {}
    for row in rows:
        if row.session_id not in sessions_seen:
            sessions_seen[row.session_id] = {
                "session_id": row.session_id,
                "preview": row.content[:80] + ("…" if len(row.content) > 80 else ""),
                "created_at": row.created_at.strftime("%b %d, %Y %H:%M"),
            }
    return jsonify(list(sessions_seen.values()))


@history_bp.route("/chats/<session_id>")
@login_required
def chat_session(session_id):
    messages = (
        ChatMessage.query.filter_by(user_id=current_user.id, session_id=session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return jsonify([m.to_dict() for m in messages])


@history_bp.route("/chats/<session_id>/load", methods=["POST"])
@login_required
def load_chat_session(session_id):
    """Switch the active chat session to a previously saved one."""
    # Verify it belongs to this user
    exists = ChatMessage.query.filter_by(
        user_id=current_user.id, session_id=session_id
    ).first()
    if not exists:
        return jsonify({"error": "Session not found."}), 404
    session["chat_session_id"] = session_id
    return jsonify({"success": True})


@history_bp.route("/chats/<session_id>/delete", methods=["POST"])
@login_required
def delete_chat_session(session_id):
    ChatMessage.query.filter_by(
        user_id=current_user.id, session_id=session_id
    ).delete()
    db.session.commit()
    return jsonify({"success": True})


@history_bp.route("/interviews")
@login_required
def interviews():
    items = (
        InterviewSession.query.filter_by(user_id=current_user.id)
        .order_by(InterviewSession.created_at.desc())
        .all()
    )
    return jsonify([i.to_dict() for i in items])
