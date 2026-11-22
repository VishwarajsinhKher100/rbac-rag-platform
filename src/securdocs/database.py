import sqlite3
from pathlib import Path
from typing import Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SQLITE_DATABASE_PATH = PROJECT_ROOT / "users.db"

DEFAULT_SEED_USERS = [
    ("alice", "pass135", "ceo"),
    ("bob", "bobhr093", "hr"),
    ("victoria", "clarapass234", "finance"),
    ("david", "davm03", "marketing"),
    ("maya", "empass934", "engineering"),
    ("william", "wilpas301", "marketing"),
    ("thomas", "paspo023", "engineering"),
    ("jack", "jakepas123", "employee"),
]


def create_sqlite_connection() -> sqlite3.Connection:
    """Create and return a SQLite database connection."""
    return sqlite3.connect(SQLITE_DATABASE_PATH)


def initialize_user_database() -> None:
    """Create the users table and seed initial user records if missing."""
    with create_sqlite_connection() as db_connection:
        db_cursor = db_connection.cursor()
        db_cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL
            )
        """)
        db_cursor.executemany(
            """
            INSERT OR IGNORE INTO users (username, password, role)
            VALUES (?, ?, ?)
            """,
            DEFAULT_SEED_USERS,
        )


def verify_user_credentials(
    username_input: str, password_input: str
) -> Tuple[bool, Optional[str]]:
    """Return whether credentials match and the assigned role, if valid."""
    with create_sqlite_connection() as db_connection:
        db_cursor = db_connection.cursor()
        db_cursor.execute(
            """
            SELECT password, role
            FROM users
            WHERE username = ?
            """,
            (username_input,),
        )
        user_record = db_cursor.fetchone()

    if user_record:
        stored_password, assigned_role = user_record
        if stored_password == password_input:
            return True, assigned_role

    return False, None
