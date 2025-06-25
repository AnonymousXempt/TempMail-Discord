import logging
import discord
from discord.ext import commands
from src.email_client import generate_new_email, retrieve_emails
import asyncio
from config import (
    DISCORD_TOKEN,
    AUTHORIZED_GUILD_ID,
    START_CHANNEL_ID,
    SESSION_TIMEOUT_SECONDS,
    EMAIL_POLL_INTERVAL,
    PRIVATE_CATEGORY_NAME,
    LOG_LEVEL
)

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

user_sessions = {}
seen_message_ids = {}
channel_lock = asyncio.Lock()

def get_active_session(user_id):
    return user_sessions.get(user_id)

def format_session_info(session):
    if session is None:
        return "No active session."
    t = session['type']
    if t == 'dm':
        return "Active session in DM."
    elif t == 'private':
        ch = session['channel']
        if ch:
            return f"Active private channel session: #{ch.name}"
        return "Active private channel session."
    elif t == 'channel':
        return f"Active public channel session (#{START_CHANNEL_ID})"
    else:
        return "Unknown session type."

async def send_new_emails_to_target(messages, user_id, send_func):
    new_messages = []
    for msg in messages:
        msg_id = msg.get("id") or msg.get("mail_id") or msg.get("uid")
        if msg_id and msg_id not in seen_message_ids.get(user_id, set()):
            new_messages.append(msg)
            seen_message_ids.setdefault(user_id, set()).add(msg_id)

    for msg in new_messages:
        subject = msg.get("subject", "No Subject")
        sender = msg.get("from", "Unknown Sender")
        body = msg.get("body_text", "[No Content]")[:1000]
        try:
            await send_func(
                f"New email from {sender}\n**Subject:** {subject}\n```\n{body}\n```"
            )
            logger.info(f"Sent email to user {user_id}: {subject}")
        except discord.Forbidden:
            logger.warning(f"Permission denied sending message to user/channel for user {user_id}")
        except Exception as e:
            logger.warning(f"Failed to send email notification for user {user_id}: {e}")

async def inbox_watcher(user_id):
    await bot.wait_until_ready()
    user = await bot.fetch_user(user_id)
    seen_message_ids[user_id] = set()
    logger.info(f"Inbox watcher started for user {user_id}")

    try:
        while True:
            email = user_sessions.get(user_id, {}).get('email')
            if not email:
                logger.info(f"Session ended for user {user_id}")
                break

            try:
                messages = retrieve_emails(email)
            except Exception as e:
                logger.error(f"Error retrieving emails for {email}: {e}")
                await asyncio.sleep(30)
                continue

            await send_new_emails_to_target(messages, user_id, user.send)
            await asyncio.sleep(EMAIL_POLL_INTERVAL)

    except asyncio.CancelledError:
        logger.info(f"Inbox watcher for user {user_id} cancelled")
        raise

@bot.command(name="start_dm")
async def start_dm(ctx):
    if ctx.guild is None or ctx.guild.id != AUTHORIZED_GUILD_ID or ctx.channel.id != START_CHANNEL_ID:
        logger.info(f"Ignored start_dm from unauthorized place by {ctx.author.id}")
        return

    user_id = ctx.author.id
    existing = get_active_session(user_id)
    if existing:
        await ctx.send(f"You already have a running session: {format_session_info(existing)}")
        return

    email = generate_new_email()
    seen_message_ids[user_id] = set()
    user = await bot.fetch_user(user_id)
    try:
        await user.send(f"Bot started. Your new temp email is: `{email}`")
    except discord.Forbidden:
        await ctx.send("Cannot send DM to you. Enable DMs from server members.")
        return

    task = bot.loop.create_task(inbox_watcher(user_id))
    user_sessions[user_id] = {'type': 'dm', 'task': task, 'email': email, 'channel': None}
    await ctx.send(f"{ctx.author.mention}, I sent you a DM.")

    async def auto_stop():
        await asyncio.sleep(SESSION_TIMEOUT_SECONDS)
        if get_active_session(user_id) and user_sessions[user_id]['type'] == 'dm':
            task.cancel()
            del user_sessions[user_id]
            seen_message_ids.pop(user_id, None)
            try:
                await user.send("Bot session ended automatically after 5 minutes.")
            except:
                pass
    bot.loop.create_task(auto_stop())

@bot.command(name="start")
async def start_channel(ctx):
    if ctx.guild is None or ctx.guild.id != AUTHORIZED_GUILD_ID or ctx.channel.id != START_CHANNEL_ID:
        return

    async with channel_lock:
        user_id = ctx.author.id
        existing = get_active_session(user_id)
        if existing:
            await ctx.send(f"You already have a running session: {format_session_info(existing)}")
            return

        email = generate_new_email()
        seen_message_ids[user_id] = set()

        await ctx.send(f"{ctx.author.mention}, temp email started: `{email}`")

        async def inbox_to_channel():
            try:
                while True:
                    messages = retrieve_emails(email)
                    await send_new_emails_to_target(messages, user_id, ctx.send)
                    await asyncio.sleep(5)
            except asyncio.CancelledError:
                logger.info(f"Inbox channel watcher for user {user_id} cancelled")
                raise
            except Exception as e:
                logger.error(f"Inbox channel watcher error for user {user_id}: {e}")
                await asyncio.sleep(10)

        task = bot.loop.create_task(inbox_to_channel())
        user_sessions[user_id] = {'type': 'channel', 'task': task, 'email': email, 'channel': ctx.channel}

        async def auto_stop():
            await asyncio.sleep(SESSION_TIMEOUT_SECONDS)
            if get_active_session(user_id) and user_sessions[user_id]['type'] == 'channel':
                task.cancel()
                del user_sessions[user_id]
                seen_message_ids.pop(user_id, None)
                try:
                    await ctx.send(f"{ctx.author.mention}, session auto-ended.")
                except:
                    pass
        bot.loop.create_task(auto_stop())

@bot.command(name="start_private")
async def start_private(ctx):
    if ctx.guild is None or ctx.guild.id != AUTHORIZED_GUILD_ID or ctx.channel.id != START_CHANNEL_ID:
        return

    user_id = ctx.author.id
    existing = get_active_session(user_id)
    if existing:
        await ctx.send(f"You already have a running session: {format_session_info(existing)}")
        return

    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        ctx.guild.me: discord.PermissionOverwrite(read_messages=True)
    }

    category = discord.utils.get(ctx.guild.categories, name=PRIVATE_CATEGORY_NAME)
    if not category:
        category = await ctx.guild.create_category(PRIVATE_CATEGORY_NAME)

    private_channel = await ctx.guild.create_text_channel(
        f"session-{ctx.author.name}-{user_id}", overwrites=overwrites, category=category
    )

    email = generate_new_email()
    seen_message_ids[user_id] = set()
    await private_channel.send(f"{ctx.author.mention}, your temp email is: `{email}`")

    async def inbox_to_private_channel():
        try:
            while True:
                messages = retrieve_emails(email)
                await send_new_emails_to_target(messages, user_id, private_channel.send)
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            logger.info(f"Inbox private channel watcher for user {user_id} cancelled")
            raise
        except Exception as e:
            logger.error(f"Inbox private channel watcher error for user {user_id}: {e}")
            await asyncio.sleep(10)

    task = bot.loop.create_task(inbox_to_private_channel())
    user_sessions[user_id] = {'type': 'private', 'task': task, 'email': email, 'channel': private_channel}

    async def auto_cleanup():
        await asyncio.sleep(SESSION_TIMEOUT_SECONDS)
        if get_active_session(user_id) and user_sessions[user_id]['type'] == 'private':
            task.cancel()
            del user_sessions[user_id]
            seen_message_ids.pop(user_id, None)
            try:
                await private_channel.send("Session ended. This channel will be deleted.")
                await asyncio.sleep(3)
                await private_channel.delete()
            except discord.Forbidden:
                logger.warning("Bot lacks permission to delete private channel")
            except Exception as e:
                logger.warning(f"Failed to delete private channel: {e}")

    bot.loop.create_task(auto_cleanup())

@bot.command(name="sessions")
async def sessions(ctx):
    user_id = ctx.author.id
    session = get_active_session(user_id)
    await ctx.send(format_session_info(session))

@bot.command(name="end")
async def end_bot(ctx):
    user_id = ctx.author.id
    session = get_active_session(user_id)

    if not session:
        await ctx.send("No active session found.")
        return

    sess_type = session['type']
    session_channel = session['channel']

    if sess_type == 'dm':
        if not isinstance(ctx.channel, discord.DMChannel):
            await ctx.send("You can only use !end for your DM session inside your DM with the bot.")
            return
    elif sess_type == 'private':
        if ctx.channel != session_channel:
            await ctx.send(f"You can only use !end inside your private session channel: #{session_channel.name}")
            return
    elif sess_type == 'channel':
        if ctx.channel.id != START_CHANNEL_ID:
            await ctx.send(f"You can only use !end in the public start channel.")
            return

    task = session['task']
    task.cancel()
    del user_sessions[user_id]
    seen_message_ids.pop(user_id, None)

    try:
        if sess_type == 'private' and session_channel:
            await session_channel.send("Session ended. Deleting this private channel.")
            await asyncio.sleep(2)
            await session_channel.delete()
        elif sess_type == 'channel' and session_channel:
            await ctx.send(f"{ctx.author.mention}, session ended. Cleaning up channel...")
            try:
                async for msg in session_channel.history(limit=100):
                    await msg.delete()
                    await asyncio.sleep(0.5)
            except Exception as e:
                logger.warning(f"Failed to clear messages in start channel on end: {e}")
        elif sess_type == 'dm':
            user = await bot.fetch_user(user_id)
            try:
                await user.send("Session ended.")
                dm_channel = await user.create_dm()
                async for msg in dm_channel.history(limit=50):
                    if msg.author == bot.user:
                        try:
                            await msg.delete()
                            await asyncio.sleep(0.5)
                        except discord.Forbidden:
                            logger.warning("Bot lacks permission to delete DM messages")
                        except Exception as e:
                            logger.warning(f"Failed to delete DM message: {e}")
            except Exception as e:
                logger.warning(f"Failed DM cleanup in end: {e}")
    except discord.Forbidden:
        logger.warning("Bot lacks permission during end cleanup")

    await ctx.send("Session ended and cleaned up.")


@bot.command(name="force_end")
async def force_end(ctx):
    user_id = ctx.author.id
    session = get_active_session(user_id)
    if not session:
        await ctx.send("No active session to force end.")
        return

    task = session['task']
    channel = session['channel']

    task.cancel()
    del user_sessions[user_id]
    seen_message_ids.pop(user_id, None)

    try:
        if session['type'] == 'private' and channel:
            await channel.send("Session forcibly ended. Deleting this private channel.")
            await asyncio.sleep(2)
            await channel.delete()
        elif session['type'] == 'channel' and channel:
            await channel.send(f"{ctx.author.mention}, session forcibly ended. Cleaning up channel...")
            try:
                async for msg in channel.history(limit=100):
                    await msg.delete()
                    await asyncio.sleep(0.5)
            except Exception as e:
                logger.warning(f"Failed to clear messages in start channel on force_end: {e}")
        elif session['type'] == 'dm':
            user = await bot.fetch_user(user_id)
            try:
                await user.send("Session forcibly ended by user.")
                dm_channel = await user.create_dm()
                async for msg in dm_channel.history(limit=50):
                    if msg.author == bot.user:
                        try:
                            await msg.delete()
                            await asyncio.sleep(0.5)
                        except discord.Forbidden:
                            logger.warning("Bot lacks permission to delete DM messages")
                        except Exception as e:
                            logger.warning(f"Failed to delete DM message: {e}")
            except Exception as e:
                logger.warning(f"Failed DM cleanup in force_end: {e}")
    except discord.Forbidden:
        logger.warning("Bot lacks permission during force_end cleanup")

    await ctx.send("Session forcibly ended and cleaned up.")


@bot.command(name="commands")
async def commands_list(ctx):
    if ctx.guild is None or ctx.guild.id != AUTHORIZED_GUILD_ID or ctx.channel.id != START_CHANNEL_ID:
        logger.info(f"Ignored commands_list from unauthorized place by {ctx.author.id}")
        return

    commands_description = """
**Available Commands:**
• `!start_dm` - Start a temp email session in your DM with the bot.
• `!start_private` - Start a temp email session in a private server channel.
• `!start` - Start a temp email session in the public start channel.
• `!end` - End your current session (must be used in the session's channel or DM).
• `!force_end` - Forcibly end your current session (usable anywhere).
• `!sessions` - Show info about your current active session.
• `!commands` - Show this commands list.
"""
    await ctx.send(commands_description)

@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user}")

def run_discord_bot():
    bot.run(DISCORD_TOKEN)

if __name__ == "__main__":
    run_discord_bot()
