"""Chat blueprint – AI mentorship chat with session history."""

import uuid
import logging
from flask import Blueprint, render_template, request, jsonify, session
from flask_login import login_required, current_user
from extensions import db
from models import ChatMessage
from ai_engine import call_granite

logger = logging.getLogger(__name__)
chat_bp = Blueprint("chat", __name__, url_prefix="/chat")


def _get_or_create_session_id() -> str:
    if not session.get("chat_session_id"):
        session["chat_session_id"] = str(uuid.uuid4())
    return session["chat_session_id"]


@chat_bp.route("/")
@login_required
def index():
    session_id = _get_or_create_session_id()
    messages = (
        ChatMessage.query.filter_by(user_id=current_user.id, session_id=session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return render_template("chat.html", messages=messages, session_id=session_id)


@chat_bp.route("/send", methods=["POST"])
@login_required
def send():
    data = request.get_json(force=True)
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"error": "Message cannot be empty."}), 400
    if len(user_message) > 2000:
        return jsonify({"error": "Message too long (max 2000 characters)."}), 400

    session_id = _get_or_create_session_id()

    # Load recent conversation history (last 10 turns for context)
    history_rows = (
        ChatMessage.query.filter_by(user_id=current_user.id, session_id=session_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(20)
        .all()
    )
    conversation_history = [{"role": r.role, "content": r.content} for r in history_rows]

    # Call AI
    ai_response = call_granite(
        user_message=user_message,
        conversation_history=conversation_history,
        max_tokens=1200,
        temperature=0.75,
    )

    # Persist both turns
    user_msg = ChatMessage(
        user_id=current_user.id,
        session_id=session_id,
        role="user",
        content=user_message,
    )
    ai_msg = ChatMessage(
        user_id=current_user.id,
        session_id=session_id,
        role="assistant",
        content=ai_response,
    )
    db.session.add_all([user_msg, ai_msg])
    db.session.commit()

    return jsonify({"reply": ai_response, "session_id": session_id})


@chat_bp.route("/new_session", methods=["POST"])
@login_required
def new_session():
    session["chat_session_id"] = str(uuid.uuid4())
    return jsonify({"session_id": session["chat_session_id"]})
