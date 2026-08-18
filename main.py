import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import yt_dlp
from apscheduler.schedulers.background import BackgroundScheduler

TELEGRAM_BOT_TOKEN = "8817519388:AAH05Kz22gJ5bey4m-9p0TwiSmme7WGmnz4"
CHANNEL_ID = "@kinoru_kgz" 

bot_app = None

async def download_and_send_audio(chat_id, query, context, is_auto=False):
    # YouTube'дун издөө роботин айланып өтүү үчүн тикелей yt-dlp search колдонобуз
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'default_search': 'ytsearch1',
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': 'song.%(ext)s',
    }
    
    try:
        if not is_auto:
            await context.bot.send_message(chat_id=chat_id, text=f"Ищу и скачиваю: {query}...")
            
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=True)
            if 'entries' in info:
                info = info['entries'][0]
            title = info.get('title', 'Музыка')
        
        with open("song.mp3", 'rb') as audio:
            await context.bot.send_audio(
                chat_id=chat_id,
                audio=audio,
                caption=f"{title}\n\nКанал: @Argen_70"
            )
        os.remove("song.mp3")
    except Exception as e:
        print(f"Ошибка: {e}")
        if not is_auto:
            await context.bot.send_message(chat_id=chat_id, text="Бул ырды табууга же жүктөөгө уруксат берилген жок. Башка ыр жазып көрүңүз.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text.lower().startswith("найти"):
        query = text[5:].strip()
        if query:
            await download_and_send_audio(update.effective_chat.id, query, context)
        else:
            await update.message.reply_text("Ырдын атын жазыңыз. Мисалы: *найти Bakr*")

def scheduled_job():
    if bot_app:
        query = "ytsearch:Top hits 2026"
        asyncio.run_coroutine_threadsafe(
            download_and_send_audio(CHANNEL_ID, query, bot_app, is_auto=True),
            bot_app.loop
        )

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    bot_app = app
    
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    scheduler = BackgroundScheduler()
    scheduler.add_job(scheduled_job, 'interval', minutes=30)
    scheduler.start()
    
    print("Бот иштеп жатат...")
    app.run_polling()
