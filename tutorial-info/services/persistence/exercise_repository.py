import hashlib
import hmac
import secrets
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

_DB_PATH = Path(__file__).parent.parent.parent / "data.db"
_initialized = False

_HASH_ALGORITHM = "pbkdf2_sha256"
_HASH_ITERATIONS = 600_000


_TODAYS_ROW = """
    SELECT id FROM exercises
    WHERE user_id = ? AND exercise_name = ? AND DATE(created_at) = DATE('now')
    ORDER BY id DESC
    LIMIT 1
"""


def _hash_password(password: str) -> str:
    """Salted PBKDF2 hash stored as 'algorithm$iterations$salt$hash'. The password itself is never stored."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _HASH_ITERATIONS)
    return f"{_HASH_ALGORITHM}${_HASH_ITERATIONS}${salt.hex()}${digest.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, iterations, salt_hex, hash_hex = stored.split("$")
        if algorithm != _HASH_ALGORITHM:
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt_hex), int(iterations)
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(digest.hex(), hash_hex)


@contextmanager
def _connect():
    """Open a short-lived connection, commit on success, roll back on error.

    One connection per call is safe across Streamlit sessions and threads,
    unlike a single shared connection.
    """
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def init_db() -> None:
    """Create the tables once per process (Streamlit calls this on every rerun)."""
    global _initialized
    if _initialized:
        return

    with _connect() as conn:
        conn.execute("PRAGMA journal_mode = WAL")  
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT UNIQUE NOT NULL,
                password_hash TEXT,
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS exercises (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id       INTEGER NOT NULL REFERENCES users(id),
                exercise_name TEXT    NOT NULL,
                reps          INTEGER NOT NULL DEFAULT 0,
                sets          INTEGER NOT NULL DEFAULT 0,
                time          INTEGER NOT NULL DEFAULT 0,
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        
        columns = [row["name"] for row in conn.execute("PRAGMA table_info(users)")]
        if "password_hash" not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")

    _initialized = True


def get_user(username: str) -> Optional[sqlite3.Row]:
    with _connect() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()


def register_user(username: str, password: str) -> sqlite3.Row:
    """Create an account. Raises ValueError if the username is already taken.

    An account made before passwords existed (no password yet) can be claimed
    by registering the same username, which sets its password.
    """
    password_hash = _hash_password(password)

    with _connect() as conn:
        created = conn.execute(
            "INSERT OR IGNORE INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash),
        )

        if created.rowcount == 0:
            claimed = conn.execute(
                "UPDATE users SET password_hash = ? WHERE username = ? AND password_hash IS NULL",
                (password_hash, username),
            )
            if claimed.rowcount == 0:
                raise ValueError("Username is already taken")

        return conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()


def authenticate(username: str, password: str) -> Optional[sqlite3.Row]:
    """Return the user row if the username and password match, otherwise None."""
    user = get_user(username)

    if user is None or not user["password_hash"]:
        return None

    return user if _verify_password(password, user["password_hash"]) else None


def add_exercise(user_id, exercise_name, reps, sets, time) -> None:
    """Add to today's row for this exercise, or create it if there isn't one."""
    with _connect() as conn:
        updated = conn.execute(
            f"""
            UPDATE exercises
            SET reps = reps + ?, sets = sets + ?, time = time + ?
            WHERE id = ({_TODAYS_ROW})
            """,
            (reps, sets, time, user_id, exercise_name),
        )

        if updated.rowcount == 0:
            conn.execute(
                """
                INSERT INTO exercises (user_id, exercise_name, sets, reps, time)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, exercise_name, sets, reps, time),
            )


def get_users_exercises(user_id):
    with _connect() as conn:
        return conn.execute(
            "SELECT * FROM exercises WHERE user_id = ? ORDER BY created_at DESC, id DESC",
            (user_id,),
        ).fetchall()