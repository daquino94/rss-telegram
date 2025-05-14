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

    success = True
    for feed_title, entries in messages_by_feed.items():
        if not entries:
            continue
            
        # Create a single message for this feed
        header = f"📢 *New content from {feed_title}*\n\n"
        entries_text = ""
        
        for entry in entries:
            entry_text = f"• *{entry['title']}*\n"
            
            # Add description if enabled and available
            if INCLUDE_DESCRIPTION and entry.get('description'):
                # Clean up the description - remove HTML tags and limit length if necessary
                description = entry['description']
                if len(description) > 150:
                    description = description[:147] + "..."
                entry_text += f"  _{description}_\n"
            
            # Add empty line and link
            entry_text += f"\n  {entry['link']}\n\n"
            
            # If adding this entry exceeds the limit, send what we have first
            if len(header) + len(entries_text) + len(entry_text) > MAX_MESSAGE_LENGTH:
                message = header + entries_text
                if not await send_telegram_message(bot, TELEGRAM_CHAT_ID, message):
                    success = False
                    
                # Start a new message
                entries_text = entry_text
            else:
                entries_text += entry_text
                
        # Send the last group of entries
        if entries_text:
            message = header + entries_text
            if not await send_telegram_message(bot, TELEGRAM_CHAT_ID, message):
                success = False
                
        # Short pause between messages from different feeds
        await asyncio.sleep(1)
    
    return success

async def check_feeds(bot):
    """Check RSS feeds for new articles."""
    sent_items = load_sent_items()
    feeds = load_feeds()
    
    if not feeds:
        logger.warning("No feeds to check. Add feeds to the configuration file.")
        return sent_items
    
    messages_by_feed = {}  # Dictionary to group notifications by feed
    
    for feed_url in feeds:
        if not feed_url.strip():
            continue
            
        logger.info(f"Checking feed: {feed_url}")
        
        try:
            feed = feedparser.parse(feed_url)
            
            if not feed.entries:
                logger.warning(f"No entries found in feed: {feed_url}")
                continue
                
            # Feed name (for message)
            feed_title = feed.feed.title if hasattr(feed.feed, 'title') else feed_url
            
            # Initialize array for this feed if it doesn't exist
            if feed_url not in sent_items:
                sent_items[feed_url] = []
                
            # Initialize array for messages from this feed
            if feed_title not in messages_by_feed:
                messages_by_feed[feed_title] = []
            
            # Check if there are new articles
            for entry in feed.entries:
                entry_id = entry.id if hasattr(entry, 'id') else entry.link
                
                # If the article hasn't been sent yet
                if entry_id not in sent_items[feed_url]:
                    # Prepare data for the message
                    title = entry.title if hasattr(entry, 'title') else "No title"
                    link = entry.link if hasattr(entry, 'link') else ""
                    
                    # Get description if needed
                    description = ""
                    if INCLUDE_DESCRIPTION:
                        if hasattr(entry, 'description'):
                            description = entry.description
                        elif hasattr(entry, 'summary'):
                            description = entry.summary
                    
                    # Add the article to the list of those to notify
                    messages_by_feed[feed_title].append({
                        'title': title,
                        'link': link,
                        'description': description
                    })
                    
                    # Add the article to the list of those sent
                    sent_items[feed_url].append(entry_id)
            
        except Exception as e:
            logger.error(f"Error checking feed {feed_url}: {e}")
    
    # Send grouped notifications
    await send_grouped_messages(bot, messages_by_feed)
    
    return sent_items

async def main_async():
    """Main asynchronous function."""
    logger.info("Starting RSS feed monitoring")
    logger.info(f"Configuration: INCLUDE_DESCRIPTION={INCLUDE_DESCRIPTION}, DISABLE_NOTIFICATION={DISABLE_NOTIFICATION}")
    
    # Check if environment variables are set
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("Missing environment variables. Make sure to set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
        return
    
    # Initialize Telegram bot
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    
    # Send startup message
    await send_telegram_message(
        bot,
        TELEGRAM_CHAT_ID,
        "🤖 *RSS Monitoring Bot started!*\nActive feed monitoring. Configuration loaded from file."
    )
    
    # Main loop
    while True:
        sent_items = await check_feeds(bot)
        save_sent_items(sent_items)
        
        logger.info(f"Next check in {CHECK_INTERVAL} seconds")
        await asyncio.sleep(CHECK_INTERVAL)

def main():
    """Main function that starts the asynchronous loop."""
    asyncio.run(main_async())

if __name__ == "__main__":
    main()