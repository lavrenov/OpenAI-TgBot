# OpenAI Telegram Bot

[![Build](https://github.com/lavrenov/OpenAI-TgBot/workflows/Deploy/badge.svg)](https://github.com/lavrenov/OpenAI-TgBot)
[![GitHub tag (latest by date)](https://img.shields.io/github/v/tag/lavrenov/OpenAI-TgBot?label=version)](https://github.com/lavrenov/OpenAI-TgBot)
[![GitHub repo size](https://img.shields.io/github/repo-size/lavrenov/OpenAI-TgBot)](https://github.com/lavrenov/OpenAI-TgBot)
[![GitHub last commit](https://img.shields.io/github/last-commit/lavrenov/OpenAI-TgBot)](https://github.com/lavrenov/OpenAI-TgBot/commits/main)

## How this is work

1. **Activate virtual environment:**
   ```
   python -m venv venv
   source venv/bin/activate
   ```
2. **Install requirements**
   ```
   pip install -r requirements.txt
   ```
3. **Configure .env**
   ```
   cp .env.sample .env
   nano .env
   ```
4. **Start**
   ```
   python main.py
   ```