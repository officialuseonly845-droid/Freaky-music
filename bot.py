import os
import asyncio
import logging
import yt_dlp
from aiohttp import web
from pyrogram import Client, filters, idle
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream, AudioQuality, VideoQuality

# ─── LOGGING ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# ─── CONFIG ─────────────────────────────────────────────────────────────────
API_ID         = int(os.getenv("API_ID", "0"))
API_HASH       = os.getenv("API_HASH", "")
BOT_TOKEN      = os.getenv("BOT_TOKEN", "")
SESSION_STRING = os.getenv("SESSION_STRING", "")

if not all([API_ID, API_HASH, BOT_TOKEN, SESSION_STRING]):
    logger.critical("❌ Env variables missing! API_ID, API_HASH, BOT_TOKEN, SESSION_STRING zaroori hain.")
    raise SystemExit(1)

# ─── CLIENTS ────────────────────────────────────────────────────────────────
bot       = Client("VideoBot",   API_ID, API_HASH, bot_token=BOT_TOKEN)
assistant = Client("Assistant",  API_ID, API_HASH, session_string=SESSION_STRING)
call_py   = PyTgCalls(assistant)

# ─── HELPERS ────────────────────────────────────────────────────────────────

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
            return f"❌ Assistant group mein join nahi kar paya:\n`{e}`"

def get_stream_url(url: str):
    """YouTube se direct CDN stream URL — koi download nahi"""
    ydl_opts = {
        "format": "best[height<=480][ext=mp4]/best[ext=mp4]/best",
        "quiet": True,
        "noplaylist": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info["url"], info.get("title", "Unknown Title")

# ─── UPTIME HTTP SERVER ──────────────────────────────────────────────────────

async def health_check(request):
    return web.Response(text="✅ Bot is alive and running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"✅ HTTP uptime server started on port {port}")

# ─── GLOBAL ERROR HANDLER ───────────────────────────────────────────────────

async def global_error_handler(_, message, exception):
    logger.error(f"Global error caught: {exception}", exc_info=exception)

# ─── COMMANDS ───────────────────────────────────────────────────────────────

@bot.on_message(filters.command("start"))
async def start_handler(_, message):
    await message.reply(
        "👋 **Video Stream Bot Online!**\n\n"
        "📌 **Commands:**\n"
        "/play `<YouTube link>` — Stream play karo\n"
        "/pause — Stream pause karo\n"
        "/resume — Stream resume karo\n"
        "/stop — Stream band karo\n\n"
        "⚡ Direct YouTube streaming — koi download nahi!"
    )

@bot.on_message(filters.command("play") & filters.group)
async def play_handler(_, message):
    try:
        if len(message.command) < 2:
            return await message.reply(
                "❌ **Usage:** `/play <YouTube link>`\n"
                "Example: `/play https://youtu.be/xxxxx`"
            )

        url = message.text.split(None, 1)[1].strip()
        m = await message.reply("⏳ Processing...")

        # Assistant ko group mein join karao
        join_status = await join_assistant(message.chat.id)
        if join_status is not True:
            return await m.edit(join_status)

        await m.edit("🔗 YouTube se stream URL fetch ho raha hai...")

        try:
            loop = asyncio.get_event_loop()
            stream_url, title = await loop.run_in_executor(None, get_stream_url, url)
        except Exception as e:
            logger.error(f"yt-dlp error: {e}")
            return await m.edit(f"❌ YouTube link se URL nahi mila:\n`{e}`")

        await m.edit("📡 Voice chat mein join ho raha hai...")

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
            logger.error(f"PyTgCalls play error: {e}")
            return await m.edit(
                f"❌ Voice chat mein stream nahi chala:\n`{e}`\n\n"
                "💡 Make sure assistant ko VC mein invite karo."
            )

        await m.edit(
            f"🎬 **Playing:** `{title}`\n\n"
            "⏸ /pause | ▶️ /resume | ⏹ /stop"
        )

    except Exception as e:
        logger.error(f"Unexpected play error: {e}", exc_info=True)
        try:
            await message.reply(f"❌ Unexpected error:\n`{e}`")
        except Exception:
            pass

@bot.on_message(filters.command("pause") & filters.group)
async def pause_handler(_, message):
    try:
        await call_py.pause_stream(message.chat.id)
        await message.reply("⏸ Stream paused.")
    except Exception as e:
        await message.reply(f"❌ Error: `{e}`")

@bot.on_message(filters.command("resume") & filters.group)
async def resume_handler(_, message):
    try:
        await call_py.resume_stream(message.chat.id)
        await message.reply("▶️ Stream resumed.")
    except Exception as e:
        await message.reply(f"❌ Error: `{e}`")

@bot.on_message(filters.command("stop") & filters.group)
async def stop_handler(_, message):
    try:
        await call_py.leave_call(message.chat.id)
        await message.reply("⏹ Stream stopped.")
    except Exception as e:
        await message.reply(f"❌ Error: `{e}`")

# ─── MAIN ───────────────────────────────────────────────────────────────────

async def main():
    try:
        await bot.start()
        logger.info("✅ Bot client started")

        await assistant.start()
        logger.info("✅ Assistant client started")

        await call_py.start()
        logger.info("✅ PyTgCalls started")

        await start_web_server()

        logger.info("🚀 Bot fully online! Waiting for messages...")
        await idle()

    except Exception as e:
        logger.critical(f"❌ Fatal startup error: {e}", exc_info=True)
        raise SystemExit(1)

    finally:
        logger.info("🛑 Shutting down...")
        try:
            await bot.stop()
            await assistant.stop()
        except Exception:
            pass

if __name__ == "__main__":
    asyncio.run(main())
