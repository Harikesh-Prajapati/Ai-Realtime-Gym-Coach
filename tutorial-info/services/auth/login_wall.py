import re
import sqlite3
import time

import streamlit as st

from services.persistence.exercise_repository import authenticate, register_user

MAX_NAME_LENGTH = 30
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128
MAX_FAILED_LOGINS = 5
LOCKOUT_SECONDS = 30
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{3,30}$")


HERO_HTML = """
<div class="auth-hero">
    <div class="auth-badge">🏋️</div>
    <div class="auth-title">AI Real-time GYM Coach</div>
    <div class="auth-sub">Live pose tracking with a coach that talks back.</div>
    <div class="auth-chips">
        <span class="auth-chip">📷 Live pose tracking</span>
        <span class="auth-chip">🎙️ AI voice coaching</span>
        <span class="auth-chip">📈 Progress history</span>
    </div>
</div>
"""


def _heading(title: str, subtitle: str):
    st.markdown(
        f'<div class="auth-form-title">{title}</div><div class="auth-form-sub">{subtitle}</div>',
        unsafe_allow_html=True,
    )


def _log_in(user):
    st.session_state.update(user_id=user["id"], username=user["username"], failed_logins=0)
    st.rerun()


def _login_form():
    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Your username", max_chars=MAX_NAME_LENGTH)
        password = st.text_input(
            "Password", type="password", placeholder="Your password", max_chars=MAX_PASSWORD_LENGTH
        )
        submitted = st.form_submit_button("Log in", type="primary", width="stretch")

    if not submitted:
        return

    wait = st.session_state.get("locked_until", 0) - time.time()
    if wait > 0:
        st.error(f"Too many failed attempts. Try again in {int(wait) + 1} seconds.")
        return

    username = username.strip()
    if not username or not password:
        st.error("Enter your username and password.")
        return

    try:
        user = authenticate(username, password)
    except sqlite3.Error:
        st.error("Could not reach the database. Please try again.")
        return

    if user is None:
        failures = st.session_state.get("failed_logins", 0) + 1
        st.session_state.failed_logins = failures
        if failures >= MAX_FAILED_LOGINS:
            st.session_state.failed_logins = 0
            st.session_state.locked_until = time.time() + LOCKOUT_SECONDS
        
        st.error("Incorrect username or password.")
        return

    _log_in(user)


def _register_form():
    with st.form("register_form"):
        username = st.text_input("Choose a username", placeholder="e.g. harikesh_01", max_chars=MAX_NAME_LENGTH)
        password = st.text_input(
            "Choose a password",
            type="password",
            placeholder=f"At least {MIN_PASSWORD_LENGTH} characters",
            max_chars=MAX_PASSWORD_LENGTH,
        )
        confirm = st.text_input(
            "Confirm password",
            type="password",
            placeholder="Repeat your password",
            max_chars=MAX_PASSWORD_LENGTH,
        )
        submitted = st.form_submit_button("Create account", type="primary", width="stretch")

    if not submitted:
        return

    username = username.strip()
    if not USERNAME_PATTERN.match(username):
        st.error("Username must be 3-30 characters: letters, numbers, dot, dash or underscore.")
    elif len(password) < MIN_PASSWORD_LENGTH:
        st.error(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    elif password != confirm:
        st.error("Passwords do not match.")
    else:
        try:
            user = register_user(username, password)
        except ValueError:
            st.error("That username is already taken.")
        except sqlite3.Error:
            st.error("Could not reach the database. Please try again.")
        else:
            _log_in(user)


def render_login_wall() -> bool:
    """Show the login / sign-up page until a user is logged in. Returns True once logged in."""
    if st.session_state.get("user_id") is not None:
        return True

    _, center, _ = st.columns([2, 3, 2])  

    with center:
        st.markdown(HERO_HTML, unsafe_allow_html=True)

        login_tab, register_tab = st.tabs(["Log in", "Create account"])

        with login_tab:
            _heading("Welcome back", "Log in to continue your training.")
            _login_form()

        with register_tab:
            _heading(
                "Create your account",
                f"Username: 3-30 letters, numbers, . - _ &nbsp;·&nbsp; Password: at least {MIN_PASSWORD_LENGTH} characters.",
            )
            _register_form()

        st.markdown(
            '<div class="auth-note">🔒 Passwords are stored as salted hashes, never as plain text.</div>',
            unsafe_allow_html=True,
        )

    return False