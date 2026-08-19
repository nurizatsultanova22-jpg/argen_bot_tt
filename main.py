import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import yt_dlp

TOKEN = "8558649634:AAHEqz0qKwSg46pcqme0D84pLsdAmVIe8p8"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    status = await update.message.reply_text("🔍 Изделүүдө...")

    try:
        # Invidious же альтернативдүү API аркылуу бөгөттү айланып өтүү
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'song.%(ext)s',
            'proxy': '', # Прокси керек болсо кошууга болот
            'quiet': True,
            'no_warnings': True,
            # YouTube API чектөөсүн четтөөнүн башка жолу - invidious экземплярларын колдонуу
            'search_suffix': '',
        }
        
        # Эгер yt-dlp түздөн-түз албаса, веб суроо аркылуу издейбиз
        search_url = f"https://pipedapi.kavin.rocks/search?q={query}&filter=music_songs"
        res = requests.get(search_url).json()
        items = res.get('items', [])
        
        if not items:
            await status.edit_text("❌ Тилекке каршы, ыр табылган жок. Башка аталышта жазып көрүңүз.")
            return
            
        track = items[0]
        title = track.get('title', 'Музыка')
        artist = track.get('uploaderName', 'Argen')
        video_id = track.get('videoId')
        
        # Аудиону жүктөө
        stream_url = f"https://pipedapi.kavin.rocks/streams/{video_id}"
        stream_res = requests.get(stream_url).json()
        audio_streams = stream_res.get('audioStreams', [])
        
        if not audio_streams:
            await status.edit_text("❌ Аудио шилтемеси ачылган жок.")
            return
            
        audio_url = audio_streams[0].get('url')
        
        # Файлды жүктөп алуу
        audio_data = requests.get(audio_url).content
        with open("song.mp3", "wb") as f:
            f.write(audio_data)
            
        await update.message.reply_audio(
            audio=open("song.mp3", "rb"),
            title=title,
            performer=artist
        )
        
        await status.delete()
        if os.path.exists("song.mp3"):
            os.remove("song.mp3")

    except Exception as e:
        await status.edit_text("⚠️ Ката кетти. Сураныч, башка ырдын атын жазып көрүңүз.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
