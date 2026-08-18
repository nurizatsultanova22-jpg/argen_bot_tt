import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from googleapiclient.discovery import build
import yt_dlp
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Сиз берген API ачкыч жана Бот токен
YOUTUBE_API_KEY = "AIzaSyAo4DTtfi2SqicLxK_zcN2CvSNYZq_gdzs"
TELEGRAM_BOT_TOKEN = "8817519388:AAH05Kz22gJ5bey4m-9p0TwiSmme7WGmnz4"
CHANNEL_ID = "@каналдын_аты"  # Ырлар автоматтык түрдө баруучу каналдын юзери (мисалы: @Argen_70_chan)

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
        if not is_auto: await context.bot.send_message(chat_id=chat_id, text="Эч нерсе табылган жок 😔")
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
        print(f"Ката: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text.lower().startswith("найти"):
        query = text[5:].strip()
        if query:
            await update.message.reply_text(f"Изделип жатат: {query}...")
            await download_and_send_audio(update.effective_chat.id, query, context)
        else:
            await update.message.reply_text("Ырдын атын жазыңыз. Мисалы: *найти Bakr*")

async def auto_post_music(context: ContextTypes.DEFAULT_TYPE):
    query = "Top new hits 2026" # Автоматтык түрдө чыкчу музыканын темасы
    await download_and_send_audio(CHANNEL_ID, query, context, is_auto=True)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    # Таймер (Ар 30 мүнөт сайын)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(auto_post_music, 'interval', minutes=30, args=[app])
    scheduler.start()
    
    print("Бот ишке кирди...")
    app.run_polling()
