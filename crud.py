from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from database import get_connection


def get_or_create_user(
    telegram_id: int,
    username: str | None,
    full_name: str,
    db_path: Path | str,
) -> int:
    """CRUD 1. Create user if not exists and return internal id."""
    with get_connection(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT OR IGNORE INTO users (telegram_id, username, full_name)
            VALUES (?, ?, ?)
            """,
            (telegram_id, username, full_name),
        )
        cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
        user_id = int(cursor.fetchone()["id"])
        connection.commit()
        return user_id


def create_poll(
    creator_id: int,
    title: str,
    description: str,
    db_path: Path | str,
) -> int:
    """CRUD 2. Create new poll in draft status."""
    with get_connection(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO polls (creator_id, title, description, status)
            VALUES (?, ?, ?, 'draft')
            """,
            (creator_id, title, description),
        )
        poll_id = int(cursor.lastrowid)
        cursor.execute(
            "INSERT INTO poll_settings (poll_id) VALUES (?)",
            (poll_id,),
        )
        connection.commit()
        return poll_id


def add_question(
    poll_id: int,
    text: str,
    question_type: str,
    position: int,
    db_path: Path | str,
) -> int:
    """CRUD 3. Add question to poll."""
    with get_connection(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO questions (poll_id, text, question_type, position)
            VALUES (?, ?, ?, ?)
            """,
            (poll_id, text, question_type, position),
        )
        connection.commit()
        return int(cursor.lastrowid)


def add_option(
    question_id: int,
    text: str,
    position: int,
    db_path: Path | str,
) -> int:
    """CRUD 4. Add answer option to question."""
    with get_connection(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO options (question_id, text, position)
            VALUES (?, ?, ?)
            """,
            (question_id, text, position),
        )
        connection.commit()
        return int(cursor.lastrowid)


def publish_poll(poll_id: int, db_path: Path | str) -> None:
    """CRUD 5. Publish poll."""
    with get_connection(db_path) as connection:
        connection.execute(
            "UPDATE polls SET status = 'active' WHERE id = ?",
            (poll_id,),
        )
        connection.commit()


def close_poll(poll_id: int, db_path: Path | str) -> None:
    """CRUD 6. Close poll."""
    with get_connection(db_path) as connection:
        connection.execute(
            "UPDATE polls SET status = 'closed' WHERE id = ?",
            (poll_id,),
        )
        connection.commit()


def delete_poll(poll_id: int, db_path: Path | str) -> None:
    """CRUD 7. Delete poll with dependent data."""
    with get_connection(db_path) as connection:
        connection.execute("DELETE FROM polls WHERE id = ?", (poll_id,))
        connection.commit()


def update_poll_title(poll_id: int, title: str, db_path: Path | str) -> None:
    """CRUD 8. Update poll title."""
    with get_connection(db_path) as connection:
        connection.execute(
            "UPDATE polls SET title = ? WHERE id = ?",
            (title, poll_id),
        )
        connection.commit()


def update_poll_description(poll_id: int, description: str, db_path: Path | str) -> None:
    """CRUD 9. Update poll description."""
    with get_connection(db_path) as connection:
        connection.execute(
            "UPDATE polls SET description = ? WHERE id = ?",
            (description, poll_id),
        )
        connection.commit()


def get_poll(poll_id: int, db_path: Path | str) -> sqlite3.Row | None:
    """CRUD 10. Get one poll."""
    with get_connection(db_path) as connection:
        return connection.execute(
            """
            SELECT polls.id, polls.title, polls.description, polls.status,
                   polls.is_anonymous, users.full_name AS creator
            FROM polls
            JOIN users ON users.id = polls.creator_id
            WHERE polls.id = ?
            """,
            (poll_id,),
        ).fetchone()


def get_active_polls(db_path: Path | str) -> list[sqlite3.Row]:
    """CRUD 11. Get active polls."""
    with get_connection(db_path) as connection:
        return connection.execute(
            """
            SELECT id, title, description, created_at
            FROM polls
            WHERE status = 'active'
            ORDER BY created_at DESC
            """
        ).fetchall()


def get_user_created_polls(user_id: int, db_path: Path | str) -> list[sqlite3.Row]:
    """CRUD 12. Get polls created by user."""
    with get_connection(db_path) as connection:
        return connection.execute(
            """
            SELECT id, title, status, created_at
            FROM polls
            WHERE creator_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,),
        ).fetchall()


def get_poll_questions(poll_id: int, db_path: Path | str) -> list[sqlite3.Row]:
    """CRUD 13. Get poll questions."""
    with get_connection(db_path) as connection:
        return connection.execute(
            """
            SELECT id, text, question_type, position
            FROM questions
            WHERE poll_id = ?
            ORDER BY position
            """,
            (poll_id,),
        ).fetchall()


def get_question_options(question_id: int, db_path: Path | str) -> list[sqlite3.Row]:
    """CRUD 14. Get options for question."""
    with get_connection(db_path) as connection:
        return connection.execute(
            """
            SELECT id, text, position
            FROM options
            WHERE question_id = ?
            ORDER BY position
            """,
            (question_id,),
        ).fetchall()


def has_user_voted_for_question(
    user_id: int,
    question_id: int,
    db_path: Path | str,
) -> bool:
    """CRUD 15. Check if user has already voted for question."""
    with get_connection(db_path) as connection:
        result = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM votes
            WHERE user_id = ? AND question_id = ?
            """,
            (user_id, question_id),
        ).fetchone()
        return int(result["count"]) > 0


def save_vote(
    user_id: int,
    poll_id: int,
    question_id: int,
    option_id: int,
    db_path: Path | str,
) -> None:
    """CRUD 16. Save vote."""
    with get_connection(db_path) as connection:
        connection.execute(
            """
            INSERT OR REPLACE INTO votes
                (user_id, poll_id, question_id, option_id)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, poll_id, question_id, option_id),
        )
        connection.commit()


def get_user_votes(user_id: int, poll_id: int, db_path: Path | str) -> list[sqlite3.Row]:
    """CRUD 17. Get user votes for poll."""
    with get_connection(db_path) as connection:
        return connection.execute(
            """
            SELECT questions.text AS question, options.text AS selected_option,
                   votes.created_at
            FROM votes
            JOIN questions ON questions.id = votes.question_id
            JOIN options ON options.id = votes.option_id
            WHERE votes.user_id = ? AND votes.poll_id = ?
            ORDER BY questions.position
            """,
            (user_id, poll_id),
        ).fetchall()


def count_votes_by_option(question_id: int, db_path: Path | str) -> list[sqlite3.Row]:
    """CRUD 18. Count votes by answer option."""
    with get_connection(db_path) as connection:
        return connection.execute(
            """
            SELECT options.id, options.text, COUNT(votes.id) AS vote_count
            FROM options
            LEFT JOIN votes ON votes.option_id = options.id
            WHERE options.question_id = ?
            GROUP BY options.id, options.text
            ORDER BY vote_count DESC, options.position
            """,
            (question_id,),
        ).fetchall()


def get_poll_results(poll_id: int, db_path: Path | str) -> list[sqlite3.Row]:
    """CRUD 19. Get full poll results."""
    with get_connection(db_path) as connection:
        return connection.execute(
            """
            SELECT questions.text AS question,
                   options.text AS option_text,
                   COUNT(votes.id) AS vote_count
            FROM questions
            JOIN options ON options.question_id = questions.id
            LEFT JOIN votes ON votes.option_id = options.id
            WHERE questions.poll_id = ?
            GROUP BY questions.id, options.id
            ORDER BY questions.position, vote_count DESC
            """,
            (poll_id,),
        ).fetchall()


def get_poll_summary(poll_id: int, db_path: Path | str) -> sqlite3.Row:
    """CRUD 20. Get summary statistics for poll."""
    with get_connection(db_path) as connection:
        return connection.execute(
            """
            SELECT polls.id, polls.title, polls.status,
                   COUNT(DISTINCT questions.id) AS question_count,
                   COUNT(DISTINCT votes.user_id) AS participant_count,
                   COUNT(votes.id) AS vote_count
            FROM polls
            LEFT JOIN questions ON questions.poll_id = polls.id
            LEFT JOIN votes ON votes.poll_id = polls.id
            WHERE polls.id = ?
            GROUP BY polls.id
            """,
            (poll_id,),
        ).fetchone()


def get_all_polls_admin(db_path: Path | str) -> list[sqlite3.Row]:
    """CRUD 21. Get all polls for dashboard/admin view."""
    with get_connection(db_path) as connection:
        return connection.execute(
            """
            SELECT polls.id, polls.title, polls.status, users.full_name AS creator,
                   polls.created_at
            FROM polls
            JOIN users ON users.id = polls.creator_id
            ORDER BY polls.created_at DESC
            """
        ).fetchall()


def create_result_export(
    poll_id: int,
    export_type: str,
    file_path: str,
    db_path: Path | str,
) -> int:
    """CRUD 22. Save export information."""
    with get_connection(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO result_exports (poll_id, export_type, file_path)
            VALUES (?, ?, ?)
            """,
            (poll_id, export_type, file_path),
        )
        connection.commit()
        return int(cursor.lastrowid)
