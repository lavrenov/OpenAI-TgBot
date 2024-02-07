import os
import telebot

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
model_gpt = os.getenv("MODEL_GPT")
max_tokens = os.getenv("MAX_TOKENS") if os.getenv("MAX_TOKENS") else None
temperature = os.getenv("TEMPERATURE") if os.getenv("TEMPERATURE") else None

bot = telebot.TeleBot(token=os.getenv("TELEGRAM_BOT_TOKEN"), parse_mode="MARKDOWN")
allowed_users = os.getenv("ALLOWED_USERS")
max_tg_msg_length = 4096

messages = []

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


def send_to_gpt(message):
    messages.append({
        "role": "user",
        "content": message
    })

    completion = client.chat.completions.create(
        model=model_gpt,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )

    message = {
        "role": completion.choices[0].message.role,
        "content": completion.choices[0].message.content
    }

    messages.append(message)


@bot.message_handler(commands=['start'])
@restricted_access
def start(message):
    user_id = message.from_user.id
    bot.reply_to(message, "Привет, Я - виртуальный помощник, готов помочь ответить на ваши вопросы и обсудить "
                          "различные темы. Чем могу помочь?")


@bot.message_handler(func=lambda message: message.text is not None and '/' not in message.text)
@restricted_access
def echo_message(message):
    user_id = message.from_user.id
    send_to_gpt(message.text)
    response_text = messages[-1]["content"]
    while len(response_text) > 0:
        response_chunk = response_text[:max_tg_msg_length]
        response_text = response_text[max_tg_msg_length:]
        bot.reply_to(message, response_chunk)


@bot.message_handler(commands=['reset'])
@restricted_access
def reset(message):
    user_id = message.from_user.id
    messages.clear()
    bot.reply_to(message, "Кеш сообщений сброшен.")


if __name__ == "__main__":
    bot.polling(none_stop=True)
