import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from googleapiclient.discovery import build
import yt_dlp
from apscheduler.schedulers.background import BackgroundScheduler

# Сиздин API ачкыч жана Бот токен
YOUTUBE_API_KEY = "AIzaSyAo4DTtfi2SqicLxK_zcN2CvSNYZq_gdzs"
TELEGRAM_BOT_TOKEN = "8817519388:AAH05Kz22gJ5bey4m-9p0TwiSmme7WGmnz4"
CHANNEL_ID = "@kinoru_kgz" 

# Глобалдык application өзгөрмөсү авто-пост үчүн
bot_app = None

# YouTube'дан музыка издөө
def search_youtube(query):
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    request = youtube.search().list(q=query, part="snippet", maxResults=1, type="video")
    response = request.execute()
    if response["items"]:
        video_id = response["items"][0]["id"]["videoId"]
        video_title = response["items"][0]["snippet"]["title"]
        return f"https://www.youtube.com/watch?v={video_id}", video_title
    return None, None

# Музыканы жүктөп, жөнөтүү
async def download_and_send_audio(chat_id, query, context, is_auto=False):
    url, title = search_youtube(query)
    if not url:
        if not is_auto: await context.bot.send_message(chat_id=chat_id, text="К сожалению, ничего не найдено 😔")
        return

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
        'outtmpl': 'song.%(ext)s',
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        with open("song.mp3", 'rb') as audio:
            await context.bot.send_audio(
                chat_id=chat_id,
                audio=audio,
                caption=f"{title}\n\nКанал: @Argen_70"
            )
        os.remove("song.mp3")
    except Exception as e:
        print(f"Ошибка: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text.lower().startswith("найти"):
        query = text[5:].strip()
        if query:
            await update.message.reply_text(f"Ищу: {query}...")
            await download_and_send_audio(update.effective_chat.id, query, context)
        else:
            await update.message.reply_text("Пожалуйста, введите название песни. Например: *найти Bakr*")

def scheduled_job():
    if bot_app:
        query = "Top new hits 2026"
        asyncio.run_coroutine_threadsafe(
            download_and_send_audio(CHANNEL_ID, query, bot_app, is_auto=True),
            bot_app.loop
        )

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    bot_app = app
    
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    # Фондо иштөөчү планировщик
    scheduler = BackgroundScheduler()
    scheduler.add_job(scheduled_job, 'interval', minutes=30)
    scheduler.start()
    
    print("Бот запущен...")
    app.run_polling()
