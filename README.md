# RSS to Telegram Bot

A Python bot that monitors RSS feeds and sends notifications to a Telegram chat when new content is published. The bot checks feeds at regular intervals, keeps track of which items have already been sent, and groups notifications by feed source for better readability.

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://buymeacoffee.com/balsamic9239)


## Features

- 📊 Monitors multiple RSS feeds from a simple text configuration file
- 📱 Sends notifications directly to a Telegram chat or channel
- 🔄 Configurable check interval
- 📦 Maintains history of sent items to avoid duplicates
- 📝 Groups notifications by feed source
- 🐳 Easy deployment with Docker

## How It Works

The bot:
1. Reads RSS feed URLs from a configuration file
2. Periodically checks each feed for new content
3. Compares entries against a history of previously sent items
4. Groups new content by feed source
5. Sends formatted notifications to Telegram
6. Updates the history file with newly sent items

## Installation

### Prerequisites

- Python 3.8+ (for local installation)
- Docker (for Docker installation)
- A Telegram bot token (get one from [@BotFather](https://t.me/BotFather))
- Your Telegram chat ID (you can use [@userinfobot](https://t.me/userinfobot))

### Option 1: Local Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/daquino94/rss-telegram.git
   cd rss-telegram
   ```

2. Install required dependencies:
   ```bash
   pip install feedparser python-telegram-bot==20.7 requests
   ```

3. Create a data directory and feeds file:
   ```bash
   mkdir -p data
   echo "# Add your RSS feeds below, one per line" > data/feeds.txt
   ```

4. Add your RSS feed URLs to `data/feeds.txt`:
   ```
   https://example.com/feed.xml
   https://anotherblog.com/rss
   ```

5. Run the bot:
   ```bash
   TELEGRAM_BOT_TOKEN="your_bot_token" TELEGRAM_CHAT_ID="your_chat_id" python rss_telegram.py
   ```

### Option 2: Docker Installation (Local Build)

1. Clone this repository:
   ```bash
   git clone https://github.com/daquino94/rss-telegram.git
   cd rss-telegram
   ```

2. Create a data directory and feeds file:
   ```bash
   mkdir -p data
   echo "# Add your RSS feeds below, one per line" > data/feeds.txt
   ```

3. Add your RSS feed URLs to `data/feeds.txt`.

4. Run the Docker container:
   ```bash
   docker build -t rss-telegram .
   docker run -d \
     --name rss-telegram \
     -e TELEGRAM_BOT_TOKEN="your_bot_token" \
     -e TELEGRAM_CHAT_ID="your_chat_id" \
     -e INCLUDE_DESCRIPTION="true" \
     -e DISABLE_NOTIFICATION="false" \
     -e CHECK_INTERVAL=3600 \
     -v $(pwd)/data:/app/data \
     rss-telegram
   ```

### Option 3: Docker Hub Installation

1. Create a directory for your data and configuration:
   ```bash
   mkdir -p rss-telegram/data
   cd rss-telegram
   echo "# Add your RSS feeds below, one per line" > data/feeds.txt
   ```

2. Add your RSS feed URLs to `data/feeds.txt`.

3. edit a docker-compose.yml with your bot token and your chat id or channel name (with @channelName)

4. Update the environment variables in docker-compose.yml with your Telegram bot token and chat ID.

5. Run the container:
   ```bash
   docker-compose up -d
   ```

   Or manually:
   ```bash
   docker run -d \
     --name rss-telegram \
     -e TELEGRAM_BOT_TOKEN="your_bot_token" \
     -e TELEGRAM_CHAT_ID="your_chat_id" \
     -e INCLUDE_DESCRIPTION="true" \
     -e DISABLE_NOTIFICATION="false" \
     -e CHECK_INTERVAL=3600 \
     -v $(pwd)/data:/app/data \
      asterix94/rss-telegram:latest
   ```

## Configuration

The bot can be configured using environment variables:

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token | Required |
| `TELEGRAM_CHAT_ID` | Your Telegram chat or channel ID | Required |
| `DISABLE_NOTIFICATION` | Disable telegram notification | false | 
| `INCLUDE_DESCRIPTION` | Include description in the message | false | 
| `CHECK_INTERVAL` | Time in seconds between feed checks | 3600 (1 hour) |
| `FEEDS_FILE` | Path to the file containing RSS feed URLs | /app/data/feeds.txt |

## Data Persistence

The bot stores two important files in the `/app/data` directory:

- `feeds.txt`: List of RSS feed URLs to monitor
- `sent_items.json`: History of already sent items (to avoid duplicates)

When using Docker, make sure to mount this directory as a volume to ensure data persistence between container restarts.

## Logs

When running with Docker, logs are stored using the json-file driver with rotation (max 3 files of 10MB each). You can view logs with:

```bash
docker logs rss-telegram
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
