from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from database import init_db, seed_db
from crud import (
    add_option,
    add_question,
    close_poll,
    count_votes_by_option,
    create_poll,
    get_active_polls,
    get_or_create_user,
    get_poll,
    get_poll_questions,
    get_poll_results,
    get_poll_summary,
    has_user_voted_for_question,
    publish_poll,
    save_vote,
    update_poll_title,
)


class PollBotTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_poll_bot.db"
        init_db(self.db_path)
        seed_db(self.db_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_create_poll(self) -> None:
        user_id = get_or_create_user(2001, "creator", "Creator User", self.db_path)
        poll_id = create_poll(user_id, "Тестовый опрос", "Описание", self.db_path)
        poll = get_poll(poll_id, self.db_path)

        self.assertEqual(poll["title"], "Тестовый опрос")
        self.assertEqual(poll["status"], "draft")

    def test_add_question_and_option(self) -> None:
        user_id = get_or_create_user(2002, "creator2", "Creator Two", self.db_path)
        poll_id = create_poll(user_id, "Опрос", "Описание", self.db_path)
        question_id = add_question(poll_id, "Ваш выбор?", "single", 1, self.db_path)
        option_id = add_option(question_id, "Вариант 1", 1, self.db_path)

        questions = get_poll_questions(poll_id, self.db_path)

        self.assertEqual(questions[0]["id"], question_id)
        self.assertIsInstance(option_id, int)

    def test_publish_and_close_poll(self) -> None:
        user_id = get_or_create_user(2003, "creator3", "Creator Three", self.db_path)
        poll_id = create_poll(user_id, "Опрос", "Описание", self.db_path)

        publish_poll(poll_id, self.db_path)
        active_polls = get_active_polls(self.db_path)
        self.assertTrue(any(poll["id"] == poll_id for poll in active_polls))

        close_poll(poll_id, self.db_path)
        poll = get_poll(poll_id, self.db_path)
        self.assertEqual(poll["status"], "closed")

    def test_save_vote(self) -> None:
        user_id = get_or_create_user(2004, "voter", "Voter User", self.db_path)
        poll_id = 1
        question_id = 1
        option_id = 1

        save_vote(user_id, poll_id, question_id, option_id, self.db_path)

        self.assertTrue(has_user_voted_for_question(user_id, question_id, self.db_path))

    def test_count_votes_by_option(self) -> None:
        result = count_votes_by_option(1, self.db_path)

        self.assertGreaterEqual(len(result), 1)
        self.assertIn("vote_count", result[0].keys())

    def test_get_poll_results_and_summary(self) -> None:
        results = get_poll_results(1, self.db_path)
        summary = get_poll_summary(1, self.db_path)

        self.assertGreaterEqual(len(results), 1)
        self.assertGreaterEqual(summary["vote_count"], 1)

    def test_update_poll_title(self) -> None:
        update_poll_title(1, "Новое название", self.db_path)
        poll = get_poll(1, self.db_path)

        self.assertEqual(poll["title"], "Новое название")


if __name__ == "__main__":
    unittest.main()
