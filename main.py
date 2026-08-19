import os
import threading
import requests
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

TOKEN = "8558649634:AAHEqz0qKwSg46pcqme0D84pLsdAmVIe8p8"

app_web = Flask(__name__)
@app_web.route('/')
def home():
    return "Bot is active!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host="0.0.0.0", port=port)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower().strip()
    
    if not (text.startswith("найди") or text.startswith("трек")):
        return  

    query = text.replace("найди", "").replace("трек", "").strip()
    if not query:
        return

    status = await update.message.reply_text("🔍 *Ищу и скачиваю трек...* 🎧", parse_mode=ParseMode.MARKDOWN)

    try:
        # Piped / Invidious API аркылуу толук аудио шилтемесин табуу (Render блокировкасын кыйгап өтөт)
        search_res = requests.get(f"https://pipedapi.kavin.rocks/search?q={query}&filter=music_songs")
        items = search_res.json().get('items', [])
        
        if not items:
            await status.edit_text("❌ *Трек не найден.*", parse_mode=ParseMode.MARKDOWN)
            return

        # Биринчи чыккан ырдын ID маалыматын алуу
        video_id = items[0]['url'].split('=')[1]
        title = items[0]['title']
        artist = items[0].get('uploader', 'Music')

        # Аудио агымын (stream) алуу үчүн Piped стримин колдонобуз
        stream_res = requests.get(f"https://pipedapi.kavin.rocks/streams/{video_id}")
        stream_data = stream_res.json()
        
        audio_streams = [s for s in stream_data.get('audioStreams', []) if s.get('mimeType', '').startswith('audio/')]
        
        if not audio_streams:
            await status.edit_text("❌ *Не удалось получить аудиофайл.*", parse_mode=ParseMode.MARKDOWN)
            return

        audio_url = audio_streams[0]['url']

        # Файлды жүктөп алуу
        mp3_file = requests.get(audio_url)
        with open('track.mp3', 'wb') as f:
            f.write(mp3_file.content)

        # Telegram'га аудио файл катары жөнөтүү
        await update.message.reply_audio(
            audio=open('track.mp3', 'rb'),
            title=title,
            performer=artist,
            caption=f"🎵 **{artist} — {title}**\n\n⚡ *Created by Argen*",
            parse_mode=ParseMode.MARKDOWN
        )
        
        await status.delete()
        if os.path.exists('track.mp3'): 
            os.remove('track.mp3')

    except Exception as e:
        await status.edit_text("❌ *Ошибка при загрузке трека.*", parse_mode=ParseMode.MARKDOWN)

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
