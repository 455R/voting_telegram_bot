from __future__ import annotations

import sqlite3
from pathlib import Path


DB_PATH = Path("poll_bot.db")


def get_connection(db_path: Path | str = DB_PATH) -> sqlite3.Connection:
    """Create SQLite connection and enable foreign keys."""
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db(db_path: Path | str = DB_PATH) -> None:
    """Create database tables."""
    with get_connection(db_path) as connection:
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL UNIQUE,
                username TEXT,
                full_name TEXT,
                is_admin INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS polls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                creator_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL DEFAULT 'draft',
                is_anonymous INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (creator_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                poll_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                question_type TEXT NOT NULL DEFAULT 'single',
                position INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (poll_id) REFERENCES polls(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS options (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                position INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                poll_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                option_id INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (poll_id) REFERENCES polls(id) ON DELETE CASCADE,
                FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
                FOREIGN KEY (option_id) REFERENCES options(id) ON DELETE CASCADE,
                UNIQUE(user_id, question_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS poll_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                poll_id INTEGER NOT NULL UNIQUE,
                allow_revote INTEGER NOT NULL DEFAULT 0,
                show_results_after_vote INTEGER NOT NULL DEFAULT 1,
                require_registration INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (poll_id) REFERENCES polls(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS result_exports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                poll_id INTEGER NOT NULL,
                export_type TEXT NOT NULL,
                file_path TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (poll_id) REFERENCES polls(id) ON DELETE CASCADE
            )
        """)

        connection.commit()


def seed_db(db_path: Path | str = DB_PATH) -> None:
    """Fill database with demo data."""
    with get_connection(db_path) as connection:
        cursor = connection.cursor()

        cursor.executemany(
            """
            INSERT OR IGNORE INTO users
                (telegram_id, username, full_name, is_admin)
            VALUES (?, ?, ?, ?)
            """,
            [
                (1001, "admin", "Администратор", 1),
                (1002, "student1", "Иван Петров", 0),
                (1003, "student2", "Мария Смирнова", 0),
                (1004, "student3", "Алексей Иванов", 0),
            ],
        )

        cursor.execute("SELECT COUNT(*) AS count FROM polls")
        if cursor.fetchone()["count"] == 0:
            cursor.execute(
                """
                INSERT INTO polls
                    (creator_id, title, description, status, is_anonymous)
                VALUES (?, ?, ?, ?, ?)
                """,
                (1, "Выбор темы семинара", "Опрос для выбора темы следующего занятия", "active", 1),
            )
            poll_id = int(cursor.lastrowid)

            cursor.execute(
                """
                INSERT INTO poll_settings
                    (poll_id, allow_revote, show_results_after_vote, require_registration)
                VALUES (?, ?, ?, ?)
                """,
                (poll_id, 0, 1, 0),
            )

            cursor.execute(
                """
                INSERT INTO questions
                    (poll_id, text, question_type, position)
                VALUES (?, ?, ?, ?)
                """,
                (poll_id, "Какую тему выбрать для семинара?", "single", 1),
            )
            question_id = int(cursor.lastrowid)

            options = [
                (question_id, "Асинхронное программирование", 1),
                (question_id, "Telegram-боты", 2),
                (question_id, "Работа с базами данных", 3),
                (question_id, "Тестирование Python-кода", 4),
            ]
            cursor.executemany(
                "INSERT INTO options (question_id, text, position) VALUES (?, ?, ?)",
                options,
            )

            cursor.executemany(
                """
                INSERT OR IGNORE INTO votes
                    (user_id, poll_id, question_id, option_id)
                VALUES (?, ?, ?, ?)
                """,
                [
                    (2, poll_id, question_id, 1),
                    (3, poll_id, question_id, 2),
                    (4, poll_id, question_id, 2),
                ],
            )

        connection.commit()
