"""
Shared user store for Project FORESIGHT.

Used by both app/dashboard.py and service/main.py so an account created
in one works in the other. Passwords are hashed with bcrypt (salted,
deliberately slow) rather than a raw SHA-256 digest — SHA-256 alone is
fast and unsalted, which makes stored passwords much easier to crack via
rainbow tables or brute force.

Storage: data/users.json. That's fine for an internship-scale deployment,
but note that on hosts with an ephemeral filesystem (a fresh container on
every redeploy), this file — and any accounts in it — can get wiped when
you push new code. Fine for a demo; if accounts need to survive redeploys
long-term, swap this for a hosted database instead.
"""

import json
from pathlib import Path

import bcrypt

USERS_FILE = Path(__file__).resolve().parent / "data" / "users.json"
USERS_FILE.parent.mkdir(parents=True, exist_ok=True)


def _load_users() -> dict:
    if not USERS_FILE.exists():
        return {}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save_users(users: dict) -> None:
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)


def create_user(username: str, password: str, name: str = "", email: str = "") -> tuple[bool, str]:
    """Register a new account. Returns (success, message)."""
    username_clean = (username or "").strip().lower()
    name = (name or "").strip()
    email = (email or "").strip()
    password = password or ""

    if not username_clean or not password:
        return False, "Username and password are both required."
    if len(username_clean) < 3:
        return False, "Username must contain at least 3 characters."
    if len(password) < 6:
        return False, "Password must contain at least 6 characters."

    users = _load_users()
    if username_clean in users:
        return False, "Username already exists. Please choose another username."

    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    users[username_clean] = {
        "name": name,
        "email": email,
        "password": password_hash,
    }
    _save_users(users)
    return True, "Account created successfully."


def verify_user(username: str, password: str) -> bool:
    """Check a username/password pair against the stored hash."""
    username_clean = (username or "").strip().lower()
    password = password or ""
    if not username_clean or not password:
        return False

    users = _load_users()
    user = users.get(username_clean)
    if not user:
        return False

    return bcrypt.checkpw(password.encode("utf-8"), user["password"].encode("utf-8"))


def get_display_name(username: str) -> str:
    username_clean = (username or "").strip().lower()
    users = _load_users()
    user = users.get(username_clean)
    if not user:
        return username_clean
    return user.get("name") or username_clean