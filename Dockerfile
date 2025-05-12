FROM python:3.11-slim

WORKDIR /app

# Installa le dipendenze
RUN pip install --no-cache-dir feedparser python-telegram-bot==20.7 requests

# Copia lo script Python
COPY rss_telegram.py .

# Crea una directory per i dati persistenti
RUN mkdir -p /app/data

# Imposta le variabili d'ambiente (da sovrascrivere con -e durante l'esecuzione)
ENV TELEGRAM_BOT_TOKEN="your_bot_token_here"
ENV TELEGRAM_CHAT_ID="your_chat_id_here"
ENV CHECK_INTERVAL=3600
ENV FEEDS_FILE="/app/data/feeds.txt"

# Esegui lo script
CMD ["python", "rss_telegram.py"]
