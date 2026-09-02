"""
LearnMate – Application Factory.
"""



import os
import uuid
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def create_app() -> Flask:
    app = Flask(__name__)

    # ── Configuration ────────────────────────────────────────────────────────
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///learnmate.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # ── Extensions ───────────────────────────────────────────────────────────
    from extensions import db, login_manager
    db.init_app(app)
    login_manager.init_app(app)

    from models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # ── DB + Seed ────────────────────────────────────────────────────────────
    with app.app_context():
        from models import User, Roadmap, ChatMessage, InterviewSession
        db.create_all()
        _seed_demo_users(db, User)

    # ── Register Blueprints ──────────────────────────────────────────────────
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.roadmap import roadmap_bp
    from routes.chat import chat_bp
    from routes.interview import interview_bp
    from routes.history import history_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(roadmap_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(interview_bp)
    app.register_blueprint(history_bp)

    # ── Root redirect ────────────────────────────────────────────────────────
    @app.route("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard.home"))
        return redirect(url_for("auth.login"))

    # ── Template helpers ─────────────────────────────────────────────────────
    @app.context_processor
    def inject_globals():
        return {"now": datetime.utcnow(), "app_name": "LearnMate"}

    return app


def _seed_demo_users(db, User):
    """Create two predefined demo accounts if they do not exist."""
    demo_accounts = [
        {
            "username": "alice",
            "email": "alice@learnmate.demo",
            "password": "Alice@123",
            "display_name": "Alice Johnson",
            "avatar_initial": "A",
        },
        {
            "username": "bob",
            "email": "bob@learnmate.demo",
            "password": "Bob@456",
            "display_name": "Bob Williams",
            "avatar_initial": "B",
        },
    ]
    for acc in demo_accounts:
        if not User.query.filter_by(username=acc["username"]).first():
            user = User(
                username=acc["username"],
                email=acc["email"],
                display_name=acc["display_name"],
                avatar_initial=acc["avatar_initial"],
            )
            user.set_password(acc["password"])
            db.session.add(user)
    db.session.commit()


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)
