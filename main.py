import os
import glob
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
from threading import Thread
from flask import Flask
import yt_dlp

TOKEN = "8558649634:AAHEqz0qKwSg46pcqme0D84pLsdAmVIe8p8"

app = Flask('')
@app.route('/')
def home(): return "Бот иштеп жатат! 🚀"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))

# YouTube'дан дароо ырды алуу үчүн жөндөө
YDL_OPTS = {
    'format': 'bestaudio/best',
    'outtmpl': 'temp_audio.%(ext)s',
    'quiet': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
}

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Салам! Ырдын атын жазсаңыз, дароо таап берем! 🎵")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    if not query: return
    
    status_msg = await update.message.reply_text("🔍 Изделүүдө жана жүктөлүүдө... ⏳")
    
    # Файлдарды тазалоо
    for f in glob.glob("temp_audio.*"): 
        try: os.remove(f)
        except: pass

    try:
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            # Издөө жана жүктөө
            res = ydl.extract_info(f"ytsearch1:{query}", download=True)
            entries = res.get('entries', [])
            if not entries:
                raise Exception("Табылган жок")
            
            entry = entries[0]
            title = entry.get('title', 'Музыка')
            thumbnail = entry.get('thumbnail')
            
            downloaded = glob.glob("temp_audio.mp3")
            if not downloaded:
                raise Exception("Жүктөө катасы")
            
            # Ырды жөнөтүү
            with open(downloaded[0], 'rb') as f:
                await update.message.reply_audio(
                    audio=f, 
                    title=title, 
                    thumbnail=thumbnail,
                    caption=f"🎵 {title}"
                )
            
            await status_msg.delete()
            # Файлды тазалоо
            os.remove(downloaded[0])
            
    except Exception as e:
        await status_msg.edit_text("❌ Тилекке каршы, бул ырды таба албадым же серверде ката кетти. Башка ыр жазып көрүңүз.")

if __name__ == "__main__":
    Thread(target=run).start()
    bot = ApplicationBuilder().token(TOKEN).build()
    bot.add_handler(CommandHandler("start", start_command))
    bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    bot.run_polling()
