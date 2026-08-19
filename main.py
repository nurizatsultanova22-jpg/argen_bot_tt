import os
import requests
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = "8558649634:AAHEqz0qKwSg46pcqme0D84pLsdAmVIe8p8"

app = Flask('')
@app.route('/')
def home(): return "Бот работает! 🚀"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    if not query: return
    
    status = await update.message.reply_text("🔍 Ищу трек...")
    
    try:
        res = requests.get(f"https://itunes.apple.com/search?term={query}&entity=song&limit=1", timeout=10)
        data = res.json()
        results = data.get('results', [])
        
        if not results:
            await status.edit_text("❌ Трек не найден.")
            return
            
        track = results[0]
        track_name = track.get('trackName', 'Музыка')
        artist_name = track.get('artistName', 'Артист')
        audio_url = track.get('previewUrl')
        
        if audio_url:
            # Файлды жүктөп алып, .mp3 катары сактап жиберебиз (документ эмес, музыка болуп барат)
            r = requests.get(audio_url)
            file_name = f"{artist_name} - {track_name}.mp3".replace("/", "_")
            with open(file_name, "wb") as f:
                f.write(r.content)
            
            with open(file_name, "rb") as audio_file:
                await update.message.reply_audio(
                    audio=audio_file,
                    title=track_name,
                    performer=artist_name,
                    caption=f"🎵 {artist_name} - {track_name}"
                )
            
            os.remove(file_name)
            await status.delete()
        else:
            await status.edit_text("❌ Не удалось получить аудиофайл.")
            
    except Exception as e:
        await status.edit_text("❌ Произошла ошибка.")

if __name__ == "__main__":
    Thread(target=run).start()
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app_bot.run_polling()
