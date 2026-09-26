"""
TerraTech — authentication layer.

Simple session-based auth using Streamlit session_state. Passwords are
hashed with PBKDF2 (see src/utils.py). Suitable for demo; not production.
"""

import streamlit as st
from src.database import get_user_by_email
from src.utils import verify_password


def check_auth() -> bool:
    """Return True if a user is logged in."""
    return st.session_state.get("authenticated", False)


def get_current_user() -> dict | None:
    """Return the logged-in user dict, or None."""
    if not check_auth():
        return None
    return st.session_state.get("user")


def get_current_role() -> str | None:
    """Return the logged-in user's role."""
    user = get_current_user()
    return user["role"] if user else None


def login(email: str, password: str) -> tuple[bool, str]:
    """
    Attempt login. Returns (success, message).

    On success, stores user in session_state.
    """
    if not email or not password:
        return False, "Please enter both email and password."

    user = get_user_by_email(email.strip().lower())
    if user is None:
        return False, "Invalid email or password."

    if not verify_password(password, user["password_hash"]):
        return False, "Invalid email or password."

    if not user.get("is_active", 1):
        return False, "This account has been deactivated."

    # Store user in session (exclude password hash)
    safe_user = {k: v for k, v in user.items() if k != "password_hash"}
    st.session_state["authenticated"] = True
    st.session_state["user"] = safe_user
    return True, "Login successful."


def logout():
    """Clear session state."""
    for key in ["authenticated", "user", "nav"]:
        st.session_state.pop(key, None)


def require_role(*roles) -> bool:
    """Check if current user has one of the specified roles."""
    user = get_current_user()
    if user is None:
        return False
    return user["role"] in roles
