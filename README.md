# Telegram-бот для голосований и опросов

## Запуск бота

1. Установить зависимости:

```bash
pip install -r requirements.txt
```

2. Получить токен у BotFather и указать его в переменной окружения:

```bash
export BOT_TOKEN="YOUR_TOKEN"
```

На Windows можно временно заменить строку в `bot.py`:

```python
BOT_TOKEN = "YOUR_TOKEN"
```

3. Запустить бота:

```bash
python bot.py
```

## Запуск дашборда

```bash
streamlit run dashboard.py
```

## Запуск тестов

```bash
python -m unittest discover -s tests
```

## Основные команды бота

- `/start`
- `/create_poll Название | Описание`
- `/add_question poll_id | Текст вопроса`
- `/add_option question_id | Текст варианта`
- `/publish poll_id`
- `/polls`
- `/my_polls`
- `/results poll_id`
- `/close poll_id`
