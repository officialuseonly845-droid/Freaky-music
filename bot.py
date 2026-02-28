import os
import shutil
import asyncio
import logging
from pyrogram import Client, filters, idle
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream
import yt_dlp
from aiohttp import web

# --- LOGGING SETUP ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# --- CONFIG ---
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
SESSION_STRING = os.getenv("SESSION_STRING")

bot = Client("VideoBot", API_ID, API_HASH, bot_token=BOT_TOKEN)
assistant = Client("Assistant", API_ID, API_HASH, session_string=SESSION_STRING)
call_py = PyTgCalls(assistant)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# --- HELPERS ---
async def join_assistant(chat_id):
    try:
        await assistant.get_chat_member(chat_id, "me")
        return True
    except Exception:
        try:
            invite_link = await bot.export_chat_invite_link(chat_id)
            await assistant.join_chat(invite_link)
            return True
        except Exception as e:
            logger.error(f"Assistant Join Error: {e}")
            return f"❌ Assistant join nahi kar paya: {e}"

def clear_downloads():
    try:
        shutil.rmtree(DOWNLOAD_DIR)
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    except Exception as e:
        logger.warning(f"Clear downloads error: {e}")

# --- UPTIME SERVER ---
async def health_check(request):
    return web.Response(text="Bot is Alive!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"✅ Web server started on port {port}")

# --- COMMANDS ---

@bot.on_message(filters.command("start"))
async def start_handler(_, message):
    await message.reply(
        "👋 **Video Bot Online Hai!**\n\n"
        "**Commands:**\n"
        "/play <link> — Video/Audio play karo\n"
        "/pause — Pause karo\n"
        "/resume — Resume karo\n"
        "/stop — Stop karo\n"
    )

@bot.on_message(filters.command("play") & filters.group)
async def play_handler(_, message):
    try:
        if len(message.command) < 2:
            return await message.reply("❌ Usage: `/play <link>`")

        url = message.text.split(None, 1)[1].strip()
        m = await message.reply("⏳ Processing...")

        join_status = await join_assistant(message.chat.id)
        if join_status is not True:
            return await m.edit(join_status)

        clear_downloads()

        ydl_opts = {
            "format": "best[height<=480][ext=mp4]/best[ext=mp4]/best",
            "outtmpl": f"{DOWNLOAD_DIR}/%(id)s.%(ext)s",
            "quiet": True,
            "noplaylist": True,
        }

        await m.edit("⬇️ Downloading...")

        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=True))
            file_path = ydl.prepare_filename(info)

        if not os.path.exists(file_path):
            return await m.edit("❌ File download nahi hui, link check karo.")

        await m.edit("📡 Streaming start ho raha hai...")
        await call_py.play(message.chat.id, MediaStream(file_path))
        await m.edit(f"🎬 **Playing:** `{info['title']}`\n\n⏸ /pause | ▶️ /resume | ⏹ /stop")

    except Exception as e:
        logger.error(f"Play Error: {e}")
        await message.reply(f"❌ Error: `{e}`")

@bot.on_message(filters.command("pause") & filters.group)
async def pause_handler(_, message):
    try:
        await call_py.pause_stream(message.chat.id)
        await message.reply("⏸ Paused.")
    except Exception as e:
        await message.reply(f"❌ Error: `{e}`")

@bot.on_message(filters.command("resume") & filters.group)
async def resume_handler(_, message):
    try:
        await call_py.resume_stream(message.chat.id)
        await message.reply("▶️ Resumed.")
    except Exception as e:
        await message.reply(f"❌ Error: `{e}`")

@bot.on_message(filters.command("stop") & filters.group)
async def stop_handler(_, message):
    try:
        await call_py.leave_call(message.chat.id)
        clear_downloads()
        await message.reply("⏹ Stopped & downloads cleared.")
    except Exception as e:
        await message.reply(f"❌ Error: `{e}`")

# --- MAIN ---
async def main():
    try:
        await bot.start()
        logger.info("✅ Bot started")
        await assistant.start()
        logger.info("✅ Assistant started")
        await call_py.start()
        logger.info("✅ PyTgCalls started")
        await start_web_server()
        logger.info("🚀 Everything is online!")
        await idle()
    except Exception as e:
        logger.critical(f"❌ Startup Failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(main())
