import os
import asyncio
import logging
import yt_dlp
from aiohttp import web
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream, AudioQuality, VideoQuality

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

API_ID         = int(os.getenv("API_ID", "0"))
API_HASH       = os.getenv("API_HASH", "")
BOT_TOKEN      = os.getenv("BOT_TOKEN", "")
SESSION_STRING = os.getenv("SESSION_STRING", "")

COOKIES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cookies.txt")

bot       = Client("VideoBot",  api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
assistant = Client("Assistant", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
call_py   = PyTgCalls(assistant)

# ─── HELPERS ─────────────────────────────────────────────────────────────────

async def join_assistant(chat_id: int):
    try:
        await assistant.get_chat_member(chat_id, "me")
        return True
    except Exception:
        try:
            invite_link = await bot.export_chat_invite_link(chat_id)
            await assistant.join_chat(invite_link)
            return True
        except Exception as e:
            logger.error(f"Assistant join error: {e}")
            return f"❌ Assistant join nahi kar paya: `{e}`"

def get_stream_url(url: str):
    ydl_opts = {
        "format": "best[height<=480][ext=mp4]/best[ext=mp4]/best",
        "quiet": True,
        "noplaylist": True,
        "no_warnings": True,
        "cookiefile": COOKIES_FILE,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info["url"], info.get("title", "Unknown")

# ─── HANDLERS ────────────────────────────────────────────────────────────────

async def start_handler(client, message):
    logger.info(f"✅ /start from {message.from_user.id}")
    await message.reply(
        "👋 **Video Stream Bot Online!**\n\n"
        "/play `<YouTube link>` — Stream play karo\n"
        "/pause — Pause karo\n"
        "/resume — Resume karo\n"
        "/stop — Stop karo"
    )

async def play_handler(client, message):
    logger.info(f"🎬 /play from {message.from_user.id} in {message.chat.id}")
    try:
        if len(message.command) < 2:
            return await message.reply("❌ Usage: `/play <YouTube link>`")

        url = message.text.split(None, 1)[1].strip()
        m = await message.reply("⏳ Processing...")

        join_status = await join_assistant(message.chat.id)
        if join_status is not True:
            return await m.edit(join_status)

        await m.edit("🔗 Stream URL fetch ho raha hai...")

        try:
            loop = asyncio.get_event_loop()
            stream_url, title = await loop.run_in_executor(None, get_stream_url, url)
        except Exception as e:
            logger.error(f"yt-dlp error: {e}")
            return await m.edit(f"❌ YouTube URL nahi mila:\n`{e}`")

        await m.edit("📡 Voice chat join ho raha hai...")

        try:
            await call_py.play(
                message.chat.id,
                MediaStream(
                    stream_url,
                    audio_quality=AudioQuality.HIGH,
                    video_quality=VideoQuality.SD_480p,
                )
            )
        except Exception as e:
            logger.error(f"PyTgCalls error: {e}")
            return await m.edit(
                f"❌ VC mein stream nahi chala:\n`{e}`\n\n"
                "💡 Assistant ko VC mein admin do (Manage Voice Chats permission)."
            )

        await m.edit(
            f"🎬 **Playing:** `{title}`\n\n"
            "⏸ /pause | ▶️ /resume | ⏹ /stop"
        )

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        await message.reply(f"❌ Error: `{e}`")

async def pause_handler(client, message):
    try:
        await call_py.pause_stream(message.chat.id)
        await message.reply("⏸ Paused.")
    except Exception as e:
        await message.reply(f"❌ {e}")

async def resume_handler(client, message):
    try:
        await call_py.resume_stream(message.chat.id)
        await message.reply("▶️ Resumed.")
    except Exception as e:
        await message.reply(f"❌ {e}")

async def stop_handler(client, message):
    try:
        await call_py.leave_call(message.chat.id)
        await message.reply("⏹ Stopped.")
    except Exception as e:
        await message.reply(f"❌ {e}")

# ─── REGISTER HANDLERS MANUALLY ──────────────────────────────────────────────

def register_handlers():
    bot.add_handler(MessageHandler(start_handler,  filters.command("start")))
    bot.add_handler(MessageHandler(play_handler,   filters.command("play")))
    bot.add_handler(MessageHandler(pause_handler,  filters.command("pause")))
    bot.add_handler(MessageHandler(resume_handler, filters.command("resume")))
    bot.add_handler(MessageHandler(stop_handler,   filters.command("stop")))
    logger.info("✅ All handlers registered")

# ─── WEB SERVER ───────────────────────────────────────────────────────────────

async def health_check(request):
    return web.Response(text="✅ Bot is alive!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"✅ HTTP server on port {port}")

# ─── MAIN ─────────────────────────────────────────────────────────────────────

async def main():
    register_handlers()

    await bot.start()
    logger.info("✅ Bot started")

    await assistant.start()
    logger.info("✅ Assistant started")

    await call_py.start()
    logger.info("✅ PyTgCalls started")

    await start_web_server()
    logger.info("🚀 Bot fully online!")

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
