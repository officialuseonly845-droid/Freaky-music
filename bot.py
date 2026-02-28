import os
import shutil
import asyncio
import logging
import yt_dlp
from aiohttp import web
from pyrogram import Client, filters, idle
from pyrogram.raw.functions.phone import CreateGroupCall, DiscardGroupCall
from ntgcalls import NTgCalls

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
SESSION_STRING = os.getenv("SESSION_STRING")

bot = Client("VideoBot", API_ID, API_HASH, bot_token=BOT_TOKEN)
assistant = Client("Assistant", API_ID, API_HASH, session_string=SESSION_STRING)
ntg = NTgCalls()

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
        logger.warning(f"Clear error: {e}")

def download_video(url):
    ydl_opts = {
        "format": "best[height<=480][ext=mp4]/best[ext=mp4]/best",
        "outtmpl": f"{DOWNLOAD_DIR}/%(id)s.%(ext)s",
        "quiet": True,
        "noplaylist": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info), info["title"]

# --- WEB SERVER ---
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
    logger.info(f"✅ Web server on port {port}")

# --- COMMANDS ---
@bot.on_message(filters.command("start"))
async def start_handler(_, message):
    await message.reply(
        "👋 **Video Bot Online!**\n\n"
        "/play <link> — Play karo\n"
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
        await m.edit("⬇️ Downloading...")

        loop = asyncio.get_event_loop()
        file_path, title = await loop.run_in_executor(None, download_video, url)

        if not os.path.exists(file_path):
            return await m.edit("❌ Download fail hua.")

        await m.edit("📡 Joining voice chat...")

        chat = await assistant.get_chat(message.chat.id)
        await ntg.play(
            message.chat.id,
            file_path,
        )

        await m.edit(f"🎬 **Playing:** `{title}`\n\n⏹ /stop")

    except Exception as e:
        logger.error(f"Play Error: {e}", exc_info=True)
        await message.reply(f"❌ Error: `{e}`")

@bot.on_message(filters.command("stop") & filters.group)
async def stop_handler(_, message):
    try:
        await ntg.stop(message.chat.id)
        clear_downloads()
        await message.reply("⏹ Stopped.")
    except Exception as e:
        await message.reply(f"❌ Error: `{e}`")

# --- MAIN ---
async def main():
    try:
        await bot.start()
        logger.info("✅ Bot started")
        await assistant.start()
        logger.info("✅ Assistant started")
        await start_web_server()
        logger.info("🚀 All systems online!")
        await idle()
    except Exception as e:
        logger.critical(f"❌ Startup Failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(main())
