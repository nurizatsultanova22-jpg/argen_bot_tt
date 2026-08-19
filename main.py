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

# YouTube жана SoundCloud'дон издөө жөндөөсү
YDL_OPTS_SEARCH = {
    'default_search': 'ytsearch1',
    'quiet': True,
    'extract_flat': False,
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
}

YDL_OPTS_DOWNLOAD = {
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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
}

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Салам! Каалаган ырдын атын жазсаңыз, дароо таап берем! 🎵")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    if not query: return
    
    search_query = query.strip()
    status_msg = await update.message.reply_text("🔍 Изделүүдө... ⏳")
    
    track_info = None
    try:
        with yt_dlp.YoutubeDL(YDL_OPTS_SEARCH) as ydl:
            res = ydl.extract_info(f"ytsearch1:{search_query}", download=False)
            entries = res.get('entries', []) if res else []
            if entries and entries[0]:
                entry = entries[0]
                track_info = {
                    'title': entry.get('title', search_query),
                    'url': entry.get('webpage_url') or entry.get('url'),
                    'thumbnail': entry.get('thumbnail')
                }
    except:
        pass

    # YouTube таппаса SoundCloud'дон издөө
    if not track_info:
        try:
            ydl_sc = dict(YDL_OPTS_SEARCH)
            ydl_sc['default_search'] = 'scsearch1'
            with yt_dlp.YoutubeDL(ydl_sc) as ydl:
                res = ydl.extract_info(f"scsearch1:{search_query}", download=False)
                entries = res.get('entries', []) if res else []
                if entries and entries[0]:
                    entry = entries[0]
                    track_info = {
                        'title': entry.get('title', search_query),
                        'url': entry.get('url'),
                        'thumbnail': entry.get('thumbnail')
                    }
        except:
            pass

    if not track_info:
        await status_msg.edit_text("❌ Тилекке каршы, эч нерсе табылган жок. Башка атын жазып көрүңүзчү! 🔍✨")
        return

    for f in glob.glob("temp_audio.*"): 
        try: os.remove(f)
        except: pass

    try:
        with yt_dlp.YoutubeDL(YDL_OPTS_DOWNLOAD) as ydl:
            ydl.extract_info(track_info['url'], download=True)
            downloaded = glob.glob("temp_audio.mp3") or glob.glob("temp_audio.*")
            if not downloaded:
                raise Exception("Файл табылган жок")
            
            file_path = downloaded[0]
            
            with open(file_path, 'rb') as f:
                await update.message.reply_audio(
                    audio=f, 
                    title=track_info['title'], 
                    thumbnail=track_info.get('thumbnail')
                )
            
            os.remove(file_path)
            await status_msg.delete()
    except Exception as e:
        for f in glob.glob("temp_audio.*"): 
            try: os.remove(f)
            except: pass
        await status_msg.edit_text("❌ Жүктөө учурунда ката кетти. Кайра жазып көрүңүз! ⚠️")

if __name__ == "__main__":
    Thread(target=run).start()
    bot = ApplicationBuilder().token(TOKEN).build()
    bot.add_handler(CommandHandler("start", start_command))
    bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    bot.run_polling()
