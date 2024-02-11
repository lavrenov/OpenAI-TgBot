import logging
import os
import sqlite3
from datetime import datetime

import telebot
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
model_gpt = os.getenv("MODEL_GPT")
max_tokens = os.getenv("MAX_TOKENS") if os.getenv("MAX_TOKENS") else None
temperature = os.getenv("TEMPERATURE") if os.getenv("TEMPERATURE") else None

bot = telebot.TeleBot(token=os.getenv("TELEGRAM_BOT_TOKEN"), parse_mode="Markdown")
allowed_users = os.getenv("ALLOWED_USERS")
max_tg_msg_length = 4096

conn = sqlite3.connect('main.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        role TEXT,
        content TEXT,
        date DATETIME
    )''')
conn.commit()

logging.basicConfig(filename="main.log", level=logging.INFO,
                    format="[%(asctime)s] [%(name)s] [%(levelname)s] > %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

if allowed_users and allowed_users.strip():
    allowed_users_list = [int(user_id.strip()) for user_id in allowed_users.split(",")]
else:
    allowed_users_list = []


def restricted_access(func):
    def wrapper(message):
        user_id = message.from_user.id
        if user_id in allowed_users_list:
            return func(message)
        else:
            bot.reply_to(message, "У вас нет доступа к этому боту.")

    return wrapper


def send_to_gpt(messages):
    completion = client.chat.completions.create(
        model=model_gpt,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )

    return completion


@bot.message_handler(commands=['start'])
@restricted_access
def start(message):
    # user_id = message.from_user.id
    bot.reply_to(message, "Привет, Я - виртуальный помощник, готов помочь ответить на ваши вопросы и обсудить "
                          "различные темы. Чем могу помочь?")


@bot.message_handler(func=lambda message: message.text is not None and '/' not in message.text)
@restricted_access
def echo_message(message):
    try:
        user_id = message.from_user.id
        text = message.text
        role = "user"
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO messages (user_id, role, content, date) VALUES (?, ?, ?, ?)",
            (user_id, role, text, current_date)
        )
        conn.commit()

        cursor.execute("SELECT role, content FROM messages WHERE user_id=? ORDER BY date ASC LIMIT 20", (user_id,))
        row = cursor.fetchall()
        messages = list(map(lambda x: {"role": x[0], "content": x[1]}, row))

        response = send_to_gpt(messages)
        role = response.choices[0].message.role
        text = response.choices[0].message.content
        response_text = text
        while len(response_text) > 0:
            response_chunk = response_text[:max_tg_msg_length]
            response_text = response_text[max_tg_msg_length:]
            bot.reply_to(message, response_chunk)

        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO messages (user_id, role, content, date) VALUES (?, ?, ?, ?)",
            (user_id, role, text, current_date)
        )
        conn.commit()
    except Exception as e:
        logging.error(e)
        bot.reply_to(message, f"Произошла ошибка при обработке вашего запроса:\n{e}")


@bot.message_handler(commands=['reset'])
@restricted_access
def reset(message):
    try:
        user_id = message.from_user.id
        bot.reply_to(message, "Кеш сообщений сброшен.")
        cursor.execute("DELETE FROM messages WHERE user_id = ?", (user_id,))
        conn.commit()
    except Exception as e:
        logging.error(e)
        bot.reply_to(message, f"Произошла ошибка при обработке вашего запроса:\n{e}")


if __name__ == "__main__":
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        logging.error(e)
