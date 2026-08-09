"""
LearnMate – SQLAlchemy database models.
"""

from datetime import datetime
from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    display_name = db.Column(db.String(120), default="Learner")
    avatar_initial = db.Column(db.String(4), default="L")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    roadmaps = db.relationship("Roadmap", backref="user", lazy=True, cascade="all, delete-orphan")
    chats = db.relationship("ChatMessage", backref="user", lazy=True, cascade="all, delete-orphan")
    interviews = db.relationship("InterviewSession", backref="user", lazy=True, cascade="all, delete-orphan")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"


class Roadmap(db.Model):
    __tablename__ = "roadmaps"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    career_goal = db.Column(db.String(200), nullable=False)
    current_skills = db.Column(db.Text, default="")
    study_hours_per_week = db.Column(db.Integer, default=10)
    experience_level = db.Column(db.String(50), default="beginner")
    content = db.Column(db.Text, nullable=False)          # AI-generated markdown
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "career_goal": self.career_goal,
            "current_skills": self.current_skills,
            "study_hours_per_week": self.study_hours_per_week,
            "experience_level": self.experience_level,
            "content": self.content,
            "created_at": self.created_at.strftime("%b %d, %Y %H:%M"),
        }


class ChatMessage(db.Model):
    __tablename__ = "chat_messages"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    session_id = db.Column(db.String(64), nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False)       # "user" | "assistant"
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at.strftime("%b %d, %Y %H:%M"),
        }


class InterviewSession(db.Model):
    __tablename__ = "interview_sessions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    job_role = db.Column(db.String(200), nullable=False)
    company_type = db.Column(db.String(100), default="tech startup")
    experience_level = db.Column(db.String(50), default="junior")
    focus_areas = db.Column(db.Text, default="")
    content = db.Column(db.Text, nullable=False)          # AI-generated prep plan
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "job_role": self.job_role,
            "company_type": self.company_type,
            "experience_level": self.experience_level,
            "focus_areas": self.focus_areas,
            "content": self.content,
            "created_at": self.created_at.strftime("%b %d, %Y %H:%M"),
        }
