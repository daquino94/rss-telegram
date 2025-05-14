#!/usr/bin/env python3
import os
import time
import json
import logging
import feedparser
from datetime import datetime
import requests
import asyncio
from telegram import Bot
from telegram.constants import ParseMode
import re
import html

# Logging configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get environment variables
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
CHECK_INTERVAL = int(os.environ.get('CHECK_INTERVAL', 3600))  # Default: 1 hour
FEEDS_FILE = os.environ.get('FEEDS_FILE', '/app/data/feeds.txt')
INCLUDE_DESCRIPTION = os.environ.get('INCLUDE_DESCRIPTION', 'false').lower() == 'true'  # Default: false
DISABLE_NOTIFICATION = os.environ.get('DISABLE_NOTIFICATION', 'false').lower() == 'true'  # Default: false
MAX_MESSAGE_LENGTH = 4096  # Maximum character limit for Telegram messages

# File to store already sent articles
HISTORY_FILE = "/app/data/sent_items.json"


def strip_html(html_content: str) -> str:
    """Convert HTML to plain text by removing tags and unescaping entities."""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', html_content)
    # Unescape HTML entities and normalize whitespace
    text = html.unescape(text)
    return ' '.join(text.split())


def load_feeds():
    """Load RSS feeds from configuration file."""
    try:
        with open(FEEDS_FILE, 'r') as f:
            feeds = [line.strip() for line in f.readlines() if line.strip() and not line.strip().startswith('#')]
            logger.info(f"Loaded {len(feeds)} feeds from {FEEDS_FILE}")
            return feeds
    except FileNotFoundError:
        logger.warning(f"Feed file {FEEDS_FILE} not found. Creating empty file...")
        with open(FEEDS_FILE, 'w') as f:
            f.write("# Add your RSS feeds here, one per line\n")
        return []
    except Exception as e:
        logger.error(f"Error loading feeds: {e}")
        return []


def load_sent_items():
    """Load history of already sent articles."""
    try:
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_sent_items(sent_items):
    """Save history of sent articles."""
    with open(HISTORY_FILE, 'w') as f:
        json.dump(sent_items, f)

async def send_telegram_message(bot, chat_id, message):
    """Send a Telegram message asynchronously."""
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode=ParseMode.MARKDOWN,
            disable_notification=DISABLE_NOTIFICATION
        )
        return True
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        return False

async def send_grouped_messages(bot, messages_by_feed):
    """Send messages grouped by feed."""
    if not messages_by_feed:
        logger.info("No new content to notify")
        return True

    for feed_title, entries in messages_by_feed.items():
        if not entries:
            continue

        header = f"📢 *New content from {feed_title}*\n\n"
        entries_text = ""

        for entry in entries:
            entry_text = f"• *{entry['title']}*\n"

            if INCLUDE_DESCRIPTION and entry.get('description'):
                desc = strip_html(entry['description'])
                if len(desc) > 150:
                    desc = desc[:147] + '...'
                entry_text += f"  _{desc}_\n"

            entry_text += f"\n  {entry['link']}\n\n"

            if len(header) + len(entries_text) + len(entry_text) > MAX_MESSAGE_LENGTH:
                await send_telegram_message(bot, TELEGRAM_CHAT_ID, header + entries_text)
                entries_text = entry_text
            else:
                entries_text += entry_text

        if entries_text:
            await send_telegram_message(bot, TELEGRAM_CHAT_ID, header + entries_text)

        await asyncio.sleep(1)

    return True

async def check_feeds(bot):
    """Check RSS feeds for new articles."""
    sent_items = load_sent_items()
    feeds = load_feeds()

    if not feeds:
        logger.warning("No feeds to check. Add feeds to the configuration file.")
        return sent_items

    messages_by_feed = {}

    for feed_url in feeds:
        if not feed_url.strip():
            continue

        logger.info(f"Checking feed: {feed_url}")

        try:
            feed = feedparser.parse(feed_url)

            if not feed.entries:
                logger.warning(f"No entries found in feed: {feed_url}")
                continue

            feed_title = feed.feed.title if hasattr(feed.feed, 'title') else feed_url
            sent_items.setdefault(feed_url, [])
            messages_by_feed.setdefault(feed_title, [])

            for entry in feed.entries:
                entry_id = entry.id if hasattr(entry, 'id') else entry.link
                if entry_id in sent_items[feed_url]:
                    continue

                title = entry.title if hasattr(entry, 'title') else "No title"
                link = entry.link if hasattr(entry, 'link') else ""
                description = ""
                if INCLUDE_DESCRIPTION:
                    description = getattr(entry, 'description', '') or getattr(entry, 'summary', '')

                messages_by_feed[feed_title].append({'title': title, 'link': link, 'description': description})
                sent_items[feed_url].append(entry_id)
        except Exception as e:
            logger.error(f"Error checking feed {feed_url}: {e}")

    await send_grouped_messages(bot, messages_by_feed)
    return sent_items

async def main_async():
    logger.info("Starting RSS feed monitoring")
    logger.info(f"Configuration: INCLUDE_DESCRIPTION={INCLUDE_DESCRIPTION}, DISABLE_NOTIFICATION={DISABLE_NOTIFICATION}")

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("Missing environment variables. Make sure to set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
        return

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    await send_telegram_message(
        bot, TELEGRAM_CHAT_ID,
        "🤖 *RSS Monitoring Bot started!*\nActive feed monitoring. Configuration loaded from file."
    )

    while True:
        sent_items = await check_feeds(bot)
        save_sent_items(sent_items)
        logger.info(f"Next check in {CHECK_INTERVAL} seconds")
        await asyncio.sleep(CHECK_INTERVAL)


def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()