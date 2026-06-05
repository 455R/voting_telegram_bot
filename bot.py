from __future__ import annotations

import asyncio
import os

from telebot.async_telebot import AsyncTeleBot
from telebot.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from database import DB_PATH, init_db, seed_db
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
    get_question_options,
    get_user_created_polls,
    has_user_voted_for_question,
    publish_poll,
    save_vote,
)


BOT_TOKEN = os.getenv("BOT_TOKEN", "7111775706:AAGj5U5-SpMngGjoz6L6yoysbtyJ5TToNz4")
bot = AsyncTeleBot(BOT_TOKEN)


def user_info(message: Message) -> tuple[int, str | None, str]:
    """Extract Telegram user data."""
    telegram_id = int(message.from_user.id)
    username = message.from_user.username
    full_name = " ".join(
        part for part in [message.from_user.first_name, message.from_user.last_name] if part
    )
    return telegram_id, username, full_name


async def send_main_menu(chat_id: int) -> None:
    """Send command list."""
    await bot.send_message(
        chat_id,
        "Бот для голосований и опросов.\n\n"
        "Команды:\n"
        "/start — регистрация и справка\n"
        "/create_poll Название | Описание — создать опрос\n"
        "/add_question poll_id | Текст вопроса — добавить вопрос\n"
        "/add_option question_id | Текст варианта — добавить вариант ответа\n"
        "/publish poll_id — опубликовать опрос\n"
        "/polls — список активных опросов\n"
        "/my_polls — мои опросы\n"
        "/results poll_id — результаты опроса\n"
        "/close poll_id — закрыть опрос",
    )


@bot.message_handler(commands=["start"])
async def start(message: Message) -> None:
    """Register user and show help."""
    telegram_id, username, full_name = user_info(message)
    get_or_create_user(telegram_id, username, full_name, DB_PATH)
    await send_main_menu(message.chat.id)


@bot.message_handler(commands=["create_poll"])
async def create_poll_handler(message: Message) -> None:
    """Create poll from command text."""
    telegram_id, username, full_name = user_info(message)
    user_id = get_or_create_user(telegram_id, username, full_name, DB_PATH)

    raw_text = message.text.replace("/create_poll", "", 1).strip()
    if "|" not in raw_text:
        await bot.send_message(
            message.chat.id,
            "Формат: /create_poll Название | Описание",
        )
        return

    title, description = [part.strip() for part in raw_text.split("|", maxsplit=1)]
    poll_id = create_poll(user_id, title, description, DB_PATH)

    await bot.send_message(
        message.chat.id,
        f"Опрос создан. ID опроса: {poll_id}\n"
        f"Теперь добавьте вопрос: /add_question {poll_id} | Текст вопроса",
    )


@bot.message_handler(commands=["add_question"])
async def add_question_handler(message: Message) -> None:
    """Add question to poll."""
    raw_text = message.text.replace("/add_question", "", 1).strip()
    if "|" not in raw_text:
        await bot.send_message(
            message.chat.id,
            "Формат: /add_question poll_id | Текст вопроса",
        )
        return

    poll_part, question_text = [part.strip() for part in raw_text.split("|", maxsplit=1)]
    poll_id = int(poll_part)

    questions = get_poll_questions(poll_id, DB_PATH)
    question_id = add_question(
        poll_id=poll_id,
        text=question_text,
        question_type="single",
        position=len(questions) + 1,
        db_path=DB_PATH,
    )

    await bot.send_message(
        message.chat.id,
        f"Вопрос добавлен. ID вопроса: {question_id}\n"
        f"Добавьте варианты: /add_option {question_id} | Текст варианта",
    )


@bot.message_handler(commands=["add_option"])
async def add_option_handler(message: Message) -> None:
    """Add answer option to question."""
    raw_text = message.text.replace("/add_option", "", 1).strip()
    if "|" not in raw_text:
        await bot.send_message(
            message.chat.id,
            "Формат: /add_option question_id | Текст варианта",
        )
        return

    question_part, option_text = [part.strip() for part in raw_text.split("|", maxsplit=1)]
    question_id = int(question_part)

    options = get_question_options(question_id, DB_PATH)
    option_id = add_option(
        question_id=question_id,
        text=option_text,
        position=len(options) + 1,
        db_path=DB_PATH,
    )

    await bot.send_message(message.chat.id, f"Вариант ответа добавлен. ID: {option_id}")


@bot.message_handler(commands=["publish"])
async def publish_handler(message: Message) -> None:
    """Publish poll."""
    parts = message.text.split()
    if len(parts) != 2:
        await bot.send_message(message.chat.id, "Формат: /publish poll_id")
        return

    poll_id = int(parts[1])
    publish_poll(poll_id, DB_PATH)
    await bot.send_message(message.chat.id, f"Опрос {poll_id} опубликован.")


@bot.message_handler(commands=["polls"])
async def active_polls_handler(message: Message) -> None:
    """Show active polls."""
    polls = get_active_polls(DB_PATH)

    if not polls:
        await bot.send_message(message.chat.id, "Активных опросов пока нет.")
        return

    markup = InlineKeyboardMarkup()
    for poll in polls:
        markup.add(
            InlineKeyboardButton(
                f"{poll['title']}",
                callback_data=f"poll_{poll['id']}",
            )
        )

    await bot.send_message(message.chat.id, "Активные опросы:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("poll_"))
async def poll_callback(call: CallbackQuery) -> None:
    """Open poll and show first question."""
    poll_id = int(call.data.split("_")[1])
    poll = get_poll(poll_id, DB_PATH)
    questions = get_poll_questions(poll_id, DB_PATH)

    if poll is None or not questions:
        await bot.answer_callback_query(call.id, "Опрос не найден или не содержит вопросов.")
        return

    question = questions[0]
    options = get_question_options(int(question["id"]), DB_PATH)

    markup = InlineKeyboardMarkup()
    for option in options:
        markup.add(
            InlineKeyboardButton(
                option["text"],
                callback_data=f"vote_{poll_id}_{question['id']}_{option['id']}",
            )
        )

    text = (
        f"Опрос: {poll['title']}\n"
        f"{poll['description']}\n\n"
        f"Вопрос: {question['text']}"
    )

    await bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.id,
        reply_markup=markup,
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("vote_"))
async def vote_callback(call: CallbackQuery) -> None:
    """Save user vote."""
    _, poll_id_str, question_id_str, option_id_str = call.data.split("_")
    poll_id = int(poll_id_str)
    question_id = int(question_id_str)
    option_id = int(option_id_str)

    full_name = " ".join(
        part for part in [call.from_user.first_name, call.from_user.last_name] if part
    )

    user_id = get_or_create_user(
        int(call.from_user.id),
        call.from_user.username,
        full_name,
        DB_PATH,
    )

    if has_user_voted_for_question(user_id, question_id, DB_PATH):
        await bot.answer_callback_query(call.id, "Вы уже голосовали по этому вопросу.")
        return

    save_vote(user_id, poll_id, question_id, option_id, DB_PATH)

    results = count_votes_by_option(question_id, DB_PATH)
    text = "Ваш голос принят.\n\nТекущие результаты:\n"
    for row in results:
        text += f"{row['text']}: {row['vote_count']}\n"

    await bot.edit_message_text(text, call.message.chat.id, call.message.id)


@bot.message_handler(commands=["results"])
async def results_handler(message: Message) -> None:
    """Show poll results."""
    parts = message.text.split()
    if len(parts) != 2:
        await bot.send_message(message.chat.id, "Формат: /results poll_id")
        return

    poll_id = int(parts[1])
    rows = get_poll_results(poll_id, DB_PATH)

    if not rows:
        await bot.send_message(message.chat.id, "Результаты не найдены.")
        return

    text = f"Результаты опроса {poll_id}:\n"
    current_question = None

    for row in rows:
        if current_question != row["question"]:
            current_question = row["question"]
            text += f"\n{current_question}\n"
        text += f"- {row['option_text']}: {row['vote_count']}\n"

    await bot.send_message(message.chat.id, text)


@bot.message_handler(commands=["my_polls"])
async def my_polls_handler(message: Message) -> None:
    """Show polls created by current user."""
    telegram_id, username, full_name = user_info(message)
    user_id = get_or_create_user(telegram_id, username, full_name, DB_PATH)

    polls = get_user_created_polls(user_id, DB_PATH)
    if not polls:
        await bot.send_message(message.chat.id, "Вы пока не создавали опросы.")
        return

    text = "Ваши опросы:\n"
    for poll in polls:
        text += f"ID {poll['id']}: {poll['title']} — {poll['status']}\n"

    await bot.send_message(message.chat.id, text)


@bot.message_handler(commands=["close"])
async def close_handler(message: Message) -> None:
    """Close poll."""
    parts = message.text.split()
    if len(parts) != 2:
        await bot.send_message(message.chat.id, "Формат: /close poll_id")
        return

    poll_id = int(parts[1])
    close_poll(poll_id, DB_PATH)
    await bot.send_message(message.chat.id, f"Опрос {poll_id} закрыт.")


if __name__ == "__main__":
    init_db(DB_PATH)
    seed_db(DB_PATH)
    print("Бот запущен")
    asyncio.run(bot.infinity_polling())
