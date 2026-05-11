"""
db.py — MongoDB helpers for NeuralChat
Collections:
    users    : { username, password_hash, created_at }
    messages : { username, role, content, timestamp }
"""

import os
import hashlib
from datetime import datetime, timezone
from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from dotenv import load_dotenv

# Load secrets from .env
load_dotenv()

# ── Connection ────────────────────────────────────────────────────────────────
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "Chat_db")


def _get_db():
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
    return client[DB_NAME]

def _ensure_indexes():
    try:
        db = _get_db()
        db.users.create_index("username", unique=True)
        db.messages.create_index([("username", ASCENDING), ("timestamp", ASCENDING)])
    except Exception:
        pass

_ensure_indexes()

# ── Password helpers ──────────────────────────────────────────────────────────
def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# ── User management ───────────────────────────────────────────────────────────
def create_user(username: str, password: str) -> tuple[bool, str]:
    try:
        db = _get_db()
        db.users.insert_one({
            "username":      username.strip().lower(),
            "password_hash": _hash(password),
            "created_at":    datetime.now(timezone.utc),
        })
        return True, "ok"
    except DuplicateKeyError:
        return False, "Username already taken."
    except ConnectionFailure:
        return False, "Cannot connect to MongoDB. Is it running?"
    except Exception as e:
        return False, str(e)


def verify_user(username: str, password: str) -> bool:
    try:
        db   = _get_db()
        user = db.users.find_one({"username": username.strip().lower()})
        if not user:
            return False
        return user["password_hash"] == _hash(password)
    except Exception:
        return False

# ── Chat history ──────────────────────────────────────────────────────────────
def save_message(username: str, role: str, content: str):
    """Persist a single chat message."""
    try:
        db = _get_db()
        db.messages.insert_one({
            "username":  username.strip().lower(),
            "role":      role,          # "user" | "assistant"
            "content":   content,
            "timestamp": datetime.now(timezone.utc),
        })
    except Exception as e:
        print(f"[DB] save_message error: {e}")


def get_chat_history(username: str, limit: int = 200) -> list[dict]:
    """Return messages for a user, oldest first."""
    try:
        db   = _get_db()
        docs = db.messages.find(
            {"username": username.strip().lower()},
            {"_id": 0, "role": 1, "content": 1, "timestamp": 1},
        ).sort("timestamp", ASCENDING).limit(limit)
        return list(docs)
    except Exception as e:
        print(f"[DB] get_chat_history error: {e}")
        return []


def get_user_stats(username: str) -> dict:
    """Return message counts for sidebar stats."""
    try:
        db    = _get_db()
        uname = username.strip().lower()
        total = db.messages.count_documents({"username": uname})
        user  = db.messages.count_documents({"username": uname, "role": "user"})
        return {"total_messages": total, "user_messages": user}
    except Exception:
        return {"total_messages": 0, "user_messages": 0}


def delete_user_history(username: str) -> int:
    """Delete all messages for a user. Returns deleted count."""
    try:
        db     = _get_db()
        result = db.messages.delete_many({"username": username.strip().lower()})
        return result.deleted_count
    except Exception:
        return 0
