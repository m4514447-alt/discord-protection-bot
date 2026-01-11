import discord
from discord.ext import commands
from datetime import timedelta
import re
import time
import os

# ========= الإعدادات =========
LOG_CHANNEL_ID = 123456789012345678  # حط ID روم اللوج
SPAM_LIMIT = 4
TIME_WINDOW = 5
MUTE_TIME = 5
# =============================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

user_spam = {}
link_regex = re.compile(r"(https?://|www\.)")

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

async def send_log(guild, text):
    channel = guild.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send(text)

async def mute_user(message, reason):
    try:
        await message.author.timeout(
            timedelta(minutes=MUTE_TIME),
            reason=reason
        )
        await send_log(
            message.guild,
            f"""🛡️ **Protection Log**
👤 User: {message.author}
📌 Reason: {reason}
📍 Channel: {message.channel.mention}
⏰ <t:{int(time.time())}:R>"""
        )
    except Exception as e:
        print("Mute error:", e)

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    if message.author.guild_permissions.administrator:
        return

    user_id = message.author.id
    now = time.time()
    content = message.content.lower()

    # روابط
    if link_regex.search(content):
        await message.delete()
        await mute_user(message, "Sending links")
        return

    # سبام
    if user_id not in user_spam:
        user_spam[user_id] = [1, now]
    else:
        count, last = user_spam[user_id]
        if now - last <= TIME_WINDOW:
            count += 1
        else:
            count = 1

        user_spam[user_id] = [count, now]

        if count >= SPAM_LIMIT:
            await message.channel.purge(
                limit=SPAM_LIMIT,
                check=lambda m: m.author.id == user_id
            )
            await mute_user(message, "Spam (4 messages)")
            user_spam[user_id] = [0, 0]
            return

    await bot.process_commands(message)

bot.run(os.getenv("TOKEN"))
