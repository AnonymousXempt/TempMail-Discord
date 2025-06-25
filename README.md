# TempMail-Discord

A Discord bot that lets users generate disposable email addresses and receive inbox messages via direct messages or commands.

---

## Description

**TempMail-Discord** is a privacy-focused Discord bot that brings temporary email functionality directly into your server. Users can generate disposable inboxes, receive emails in real-time, and auto-expire sessions all within Discord.

It’s built for anyone who values privacy or needs to quickly generate temp emails without relying on a browser. Whether you're testing signups or want to avoid spam, **TempMail-Discord** gives you seamless inbox access right from Discord.

---

## Features

- **Generate disposable email addresses** instantly with a single command (`!start`, `!start_dm`, `!start_private`)
- **Real-time inbox monitoring** with automatic polling and delivery of new messages
- **Support for three session types:**
	- **DM sessions** – Direct private messages from the bot
	- **Private channel sessions** – Isolated channels only visible to the user and bot
	- **Public start channel sessions** – All users can initiate temp mail in a designated channel
- **Automatic session timeout** – Sessions auto-end after a configurable period of inactivity
- **Session cleanup** - Deletes private channels or clears messages when a session ends
- **Permission-aware** – Only responds in the authorized server and channel, respects DM permissions
- **Simple configuration** - Manage behavior using `.env` and `config.py`
- **Minimal dependencies**  and lightweight footprint

---

## Installation

1. **Clone the repository**
   ```
   git clone https://github.com/AnonymousXempt/TempMail-Discord.git
   ```

2. **Navigate into the project directory**
   ```
   cd tempmail-discord
   ```

3. **Install dependencies**
   ```
   pip install -r requirements.txt
   ```

---

## Create Discord bot

To use **TempMail-Discord**, you need to create a Discord bot application and invite it to your server with the appropriate permissions.

### Steps to Create the Bot

1. Go to the Discord Developer Portal and log in.
2. Click New Application, give it a name (e.g., TempMail-Bot), and create it.
3. Navigate to the Bot tab, then click Add Bot to create the bot user.
4. Under Token, click Copy to save your bot token. This goes into your `.env` file as `DISCORD_TOKEN`.

### Setting Bot Permissions

Bot Permissions:

- Send Messages
- Read Message History
- Manage Messages
- View Channels
- Manage Channels

### Generating the Invite Link

1. Under OAuth2 > URL Generator, select the scopes and permissions above (or alternatively configure in server roles).
2. Copy the generated invite URL and open it in your browser.
3. Select your server and authorize the bot.

## How to Enable Developer Mode & Copy Server and Channel IDs

To configure TempMail-Discord, you need your Discord Server ID and Start Channel ID. These are not visible by default but can be obtained by enabling Developer Mode.

### Enable Developer Mode in Discord Client

1. Open your Discord app.
2. Click the User Settings gear icon (bottom-left corner).
3. On the left sidebar, scroll down and click Advanced.
4. Toggle Developer Mode ON.

### How to Copy Server (Guild) ID

1. Go to your Discord server.
2. Right-click on the server icon in the left sidebar.
3. Click Copy ID. Paste this value into your `.env` as `AUTHORIZED_GUILD_ID`.

### How to Copy Channel ID

1. Go to the channel where you want users to start sessions.
2. Right-click the channel name in the channel list.
3. Click Copy ID. Paste this value into your `.env` as `START_CHANNEL_ID`.

---

## Configure .env File 

You can customize the bots behaviour and authorised channels by modifying the `.env` file.

### Example `.env` File

```env
DISCORD_TOKEN=your_discord_bot_token
AUTHORIZED_GUILD_ID=your_server_id
START_CHANNEL_ID=your_channel_id
SESSION_TIMEOUT_SECONDS=300
EMAIL_POLL_INTERVAL=5
PRIVATE_CATEGORY_NAME=Private TempMail Sessions
LOG_LEVEL=INFO
```

---
## Usage

Run the tool with:

```
python main.py
```

### Command Options:
- `!start_dm`: Start a temporary email session via direct message with the bot
- `!start_private`: Start a temporary email session in a private server channel just for you
- `!start`: Start a temporary email session in the public start channel
- `!sessions`: Show information about your current active session
- `!end`: End your current session (must be used inside the session’s channel or DM)
- `!force_end`: Forcibly end your current session from anywhere (use with caution)
- `!commands`: Display this list of available commands

### Session Behaviour
- Sessions automatically auto-refresh inbox every 5 seconds
- Sessions auto-timeout and clean up after a configured period of inactivity (default 5 minutes)
---

## Screenshot

![Screenshot 2025-06-25 152737](https://github.com/user-attachments/assets/d7bc7404-5977-4e51-9a20-5b585ea14afd)

---

## Roadmap

- [x] **CLI App** – Fully functional terminal interface to generate and monitor temp emails in real-time [(Goto)](https://github.com/AnonymousXempt/TempMail-CLI)
- [ ] Bot Integrations
   - [x] **Discord Bot** – Interact with temp mail features using bot commands or DMs
   - [ ] **Telegram Bot** – Lightweight access via chat interface, ideal for mobile usage
- [ ] **PyPI Package** - Publish as a pip-installable package (tempmail-cli) for simpler installation and updates

---

## License

This project is licensed under the **MIT License**.  
See the [`LICENSE`](./LICENSE) file for details.

## Acknowledgments
This project leverages the Temp-Mail API: https://api.internal.temp-mail.io/api/v3 for generating and retrieving temporary emails.
