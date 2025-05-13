FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir feedparser python-telegram-bot==20.7 requests

COPY rss_telegram.py .

RUN mkdir -p /app/data

ENV TELEGRAM_BOT_TOKEN="your_bot_token_here"
ENV TELEGRAM_CHAT_ID="your_chat_id_here"
ENV INCLUDE_DESCRIPTION="true"
ENV DISABLE_NOTIFICATION="false"
ENV CHECK_INTERVAL=3600
ENV FEEDS_FILE="/app/data/feeds.txt"

CMD ["python", "rss_telegram.py"]
