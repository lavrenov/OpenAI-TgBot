import asyncio
import atexit
import logging
import os
from datetime import datetime

from aiogram import Dispatcher, F, Bot
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from dotenv import load_dotenv
from openai import OpenAI

import db

logging.basicConfig(
    filename="main.log",
    level=logging.INFO,
    format="[%(asctime)s] [%(name)s] [%(levelname)s] > %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

load_dotenv()
dp = Dispatcher()

telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
allowed_users = os.getenv("ALLOWED_USERS")

if allowed_users and allowed_users.strip():
    allowed_users = {int(user_id.strip()) for user_id in allowed_users.split(",")}
else:
    allowed_users = {}

client = OpenAI(
    base_url=os.getenv("OPENAI_BASE_URL"),
    api_key=os.getenv("OPENAI_API_KEY")
)
model_gpt = os.getenv("MODEL_GPT")
max_tokens = os.getenv("MAX_TOKENS") if os.getenv("MAX_TOKENS") else None
temperature = os.getenv("TEMPERATURE") if os.getenv("TEMPERATURE") else None


def send_to_gpt(messages):
    completion = client.chat.completions.create(
        model=model_gpt,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )

    return completion


@dp.message(CommandStart(), F.from_user.id.in_(allowed_users))
async def command_start_handler(message: Message) -> None:
    try:
        name = message.from_user.full_name
        await message.answer(f"Привет, {name}. Я - виртуальный помощник, готов помочь ответить на ваши вопросы и "
                             f"обсудить различные темы. Чем могу помочь?")
    except Exception as e:
        logging.error(e)
        await message.answer(f"Произошла ошибка при обработке вашего запроса:\n{e}")


@dp.message(Command("reset"), F.from_user.id.in_(allowed_users))
async def message_handler(message: Message) -> None:
    try:
        user_id = message.from_user.id
        with db.connect() as conn:
            cursor = conn.cursor()
            sql = "DELETE FROM messages WHERE user_id = ?"
            cursor.execute(sql, (user_id,))
            conn.commit()
        await message.answer("Кеш сообщений сброшен.")
    except Exception as e:
        logging.error(e)
        await message.answer(f"Произошла ошибка при обработке вашего запроса:\n{e}")


@dp.message(F.from_user.id.in_(allowed_users))
async def message_handler(message: Message) -> None:
    try:
        user_id = message.from_user.id
        text = message.text
        role = "user"
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with db.connect() as conn:
            cursor = conn.cursor()
            sql = "INSERT INTO messages (user_id, role, content, date) VALUES (?, ?, ?, ?)"
            cursor.execute(sql, (user_id, role, text, current_date))
            conn.commit()

            cursor.execute("SELECT role, content FROM messages WHERE user_id=? ORDER BY date ASC LIMIT 20", (user_id,))
            messages = cursor.fetchall()

        response = send_to_gpt(messages)
        role = response.choices[0].message.role
        text = response.choices[0].message.content
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with db.connect() as conn:
            cursor = conn.cursor()
            sql = "INSERT INTO messages (user_id, role, content, date) VALUES (?, ?, ?, ?)"
            cursor.execute(sql, (user_id, role, text, current_date))
            conn.commit()
        await message.answer(text, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logging.error(e)
        await message.answer(f"Произошла ошибка при обработке вашего запроса:\n{e}")


async def main() -> None:
    bot = Bot(telegram_bot_token)
    await dp.start_polling(bot)


atexit.register(db.close)

if __name__ == "__main__":
    db.init()
    asyncio.run(main())
