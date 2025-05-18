# Slack to Discord Migration Bot

A Discord bot designed to migrate content from Slack to Discord channels. This bot was built for [Makerspace Delft](https://www.makespacedelft.nl/) to facilitate their migration from Slack to Discord in 2023.

## Overview

This bot provides two main sets of functionality:

1. **Slack Migration Tools**: Commands to migrate messages, threads, and files from Slack to Discord with user information preservation
2. **Channel Management**: Tools to create and manage channels and permissions within Discord

## Features

### Slack Migration

- Migrate public Slack channels to Discord
- Migrate private Slack channels to Discord
- Preserve conversation threads
- Migrate file attachments (up to 8MB per file)
- Preserve user names and profile pictures
- Format Slack messages for Discord compatibility

### Channel Management

- Create text and voice channels
- Set channel visibility (public/private)
- Add and remove users from channels
- Organize channels in categories
- Role-based permission management

## Prerequisites

- Python 3.10+
- A Discord Bot Token
- A Slack API Token with permissions to read channels

## Setup and Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/slack-discord-migration-bot.git
cd slack-discord-migration-bot
```

2. Copy the sample environment file and fill in your tokens
```bash
cp .env.sample .env
```

3. Edit the `.env` file with your Discord and Slack tokens:
```
DISCORD_TOKEN=your_discord_bot_token
SLACK_TOKEN=your_slack_api_token
```

4. Install required packages
```bash
pip install -r requirements.txt
```

5. Run the bot
```bash
python main.py
```

**Note:** Do not use production tokens in your local .env file when testing.

## Commands

### Migration Commands

| Command | Description |
|---------|-------------|
| `/sync` | Synchronize slash commands with Discord |
| `/migrate <channelid> [limit] [after]` | Migrate messages from a public Slack channel |
| `/migrateprivate <channelid> [limit]` | Migrate messages from a private Slack channel |
| `/ditto <name> <message>` | Send a message as another user (admin only) |

### Channel Management Commands

| Command | Description |
|---------|-------------|
| `/createchannel <group> <name> [visibility]` | Create a text channel in a category |
| `/createvoicechannel <group> <name> [visibility]` | Create a voice channel in a category |
| `/addtotextchannel <channel> <user>` | Add a user to a text channel |
| `/removefromtextchannel <channel> <user>` | Remove a user from a text channel |
| `/addtovoicechannel <channel> <user>` | Add a user to a voice channel |
| `/removefromvoicechannel <channel> <user>` | Remove a user from a voice channel |

### Other Commands

| Command | Description |
|---------|-------------|
| `!ping` | Simple ping-pong response to check if the bot is running |

## Deployment

This bot includes configuration for deployment on [Fly.io](https://fly.io):

1. Install the Fly.io CLI tools
2. Set up a GitHub Actions workflow with your FLY_API_TOKEN
3. Push to the main branch to automatically deploy

## Limitations and Disclaimers

- This bot was built in 2023 and uses APIs that may have changed since then
- Discord and Slack APIs are subject to change, so some functionality may require updates
- File migration is limited to 8MB per file due to Discord's file size limits
- Profile pictures may occasionally be inconsistent due to API limitations
- The bot requires appropriate permissions in both Slack and Discord to function properly

---

*This bot was created for [Makerspace Delft](https://www.makespacedelft.nl/) to facilitate migration from Slack to Discord. It can be adapted for other communities with similar migration needs.*