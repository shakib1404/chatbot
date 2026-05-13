"""
db.py — MongoDB helpers for NeuralChat
Collections:
    users         : { username, password_hash, created_at }
    chats         : { username, title, created_at, updated_at }
    messages      : { username, chat_id, role, content, timestamp }
"""

import os
import hashlib
import uuid
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
        db.chats.create_index([("chat_id", ASCENDING)], unique=True)
        db.chats.create_index([("username", ASCENDING), ("updated_at", ASCENDING)])
        db.messages.create_index([("username", ASCENDING), ("chat_id", ASCENDING), ("timestamp", ASCENDING)])
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
def create_chat_session(username: str, title: str | None = None) -> str:
    """Create a new chat session and return its id."""
    try:
        db = _get_db()
        now = datetime.now(timezone.utc)
        chat_id = uuid.uuid4().hex
        result = db.chats.insert_one({
            "chat_id": chat_id,
            "username": username.strip().lower(),
            "title": title or "New chat",
            "summary": "",
            "created_at": now,
            "updated_at": now,
        })
        return chat_id
    except Exception as e:
        print(f"[DB] create_chat_session error: {e}")
        return ""


def list_chat_sessions(username: str, limit: int = 50) -> list[dict]:
    """Return chat sessions for a user, newest first."""
    try:
        db = _get_db()
        docs = db.chats.find(
            {"username": username.strip().lower()},
            {"_id": 0, "chat_id": 1, "title": 1, "summary": 1, "created_at": 1, "updated_at": 1},
        ).sort("updated_at", ASCENDING).limit(limit)
        sessions = list(docs)
        sessions.reverse()
        return sessions
    except Exception as e:
        print(f"[DB] list_chat_sessions error: {e}")
        return []


def rename_chat_session(chat_id: str, title: str):
    """Rename a chat session."""
    try:
        db = _get_db()
        db.chats.update_one(
            {"chat_id": chat_id},
            {"$set": {"title": title, "updated_at": datetime.now(timezone.utc)}},
        )
    except Exception as e:
        print(f"[DB] rename_chat_session error: {e}")


def touch_chat_session(chat_id: str):
    """Update the session's last activity time."""
    try:
        db = _get_db()
        db.chats.update_one(
            {"chat_id": chat_id},
            {"$set": {"updated_at": datetime.now(timezone.utc)}},
        )
    except Exception as e:
        print(f"[DB] touch_chat_session error: {e}")


def update_chat_summary(chat_id: str, summary: str):
    """Update rolling summary for a chat session."""
    try:
        db = _get_db()
        db.chats.update_one(
            {"chat_id": chat_id},
            {
                "$set": {
                    "summary": summary.strip(),
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
    except Exception as e:
        print(f"[DB] update_chat_summary error: {e}")


def save_message(username: str, role: str, content: str, chat_id: str | None = None):
    """Persist a single chat message."""
    try:
        db = _get_db()
        db.messages.insert_one({
            "username":  username.strip().lower(),
            "chat_id":   chat_id,
            "role":      role,          # "user" | "assistant"
            "content":   content,
            "timestamp": datetime.now(timezone.utc),
        })
    except Exception as e:
        print(f"[DB] save_message error: {e}")


def get_chat_history(username: str, chat_id: str | None = None, limit: int = 200) -> list[dict]:
    """Return messages for a user and chat session, oldest first."""
    try:
        db   = _get_db()
        query = {"username": username.strip().lower()}
        if chat_id:
            query["chat_id"] = chat_id
        docs = db.messages.find(
            query,
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
        uname = username.strip().lower()
        result = db.messages.delete_many({"username": uname})
        db.chats.delete_many({"username": uname})
        return result.deleted_count
    except Exception:
        return 0
