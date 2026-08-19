import os
import yt_dlp
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

TOKEN = "8558649634:AAHEqz0qKwSg46pcqme0D84pLsdAmVIe8p8"

app = Flask('')
@app.route('/')
def home(): return "Бот работает! 🚀"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))

# Колдонуучу катталганда чыгуучу саламдашуу
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 Салам! Мен Argenдин музыкалык ботумун.\n\n"
        "Мага каалаган ырыңыздын атын жазыңыз, мен аны толук версияда таап, сизге жөнөтөм. 🎵"
    )
    await update.message.reply_text(welcome_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    if not query: return
    
    status = await update.message.reply_text("🔍 Издейм...")
    
    try:
        ydl_opts = {
            'format': 'bestaudio',
            'outtmpl': 'song.mp3',
            'quiet': True,
            'no_warnings': True,
            'default_search': 'scsearch1'
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=True)
            if 'entries' in info:
                entry = info['entries'][0]
            else:
                entry = info
                
            title = entry.get('title', 'Музыка')
            uploader = entry.get('uploader', 'SoundCloud')
        
        if os.path.exists('song.mp3'):
            with open('song.mp3', 'rb') as audio_file:
                await update.message.reply_audio(
                    audio=audio_file,
                    title=title,
                    performer=uploader,
                    caption=f"🎵 {uploader} - {title}"
                )
            os.remove('song.mp3')
            await status.delete()
        else:
            await status.edit_text("❌ Файл табылган жок.")
            
    except Exception as e:
        await status.edit_text("❌ Ыр табылган жок же ката чыкты.")

if __name__ == "__main__":
    Thread(target=run).start()
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start)) # /start командасын кошуу
    app_bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app_bot.run_polling()
