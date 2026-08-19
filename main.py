import os
import requests
import yt_dlp
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = "8558649634:AAHEqz0qKwSg46pcqme0D84pLsdAmVIe8p8"

app = Flask('')
@app.route('/')
def home(): return "Бот работает! 🚀"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))

# Толук ырды алуу үчүн конфигурация
ydl_opts = {
    'format': 'bestaudio/best',
    'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
    'outtmpl': 'music.mp3',
    'quiet': True
}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    status = await update.message.reply_text("🔍 Ищу полную версию трека...")
    
    try:
        # YouTube'дан издөө
        with yt_dlp.YoutubeDL({'default_search': 'ytsearch1', 'quiet': True}) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)['entries'][0]
            url = info['webpage_url']
            title = info['title']
        
        # Толук ырды жүктөө
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        # Telegram'га аудио катары жөнөтүү
        with open('music.mp3', 'rb') as audio:
            await update.message.reply_audio(
                audio=audio,
                title=title,
                caption=f"🎵 {title}"
            )
        
        os.remove('music.mp3')
        await status.delete()
            
    except Exception as e:
        await status.edit_text("❌ Ошибка: не удалось скачать полную версию.")

if __name__ == "__main__":
    Thread(target=run).start()
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app_bot.run_polling()
