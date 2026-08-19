import os
import glob
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes
from threading import Thread
from flask import Flask
import yt_dlp

TOKEN = "8558649634:AAHEqz0qKwSg46pcqme0D84pLsdAmVIe8p8"

app = Flask('')
@app.route('/')
def home(): return "Бот работает! 🚀"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))

search_cache = {}

YDL_OPTS_SEARCH = {
    'default_search': 'ytsearch5',
    'quiet': True,
    'extract_flat': True,
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
}

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["🔥 Популярное", "🎧 Новинки"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Привет! Напиши название песни или исполнителя, и я найду их для тебя! 🎵", 
        reply_markup=reply_markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    query = update.message.text
    if not query: return
    
    if query == "🔥 Популярное": query = "Хиты 2026"
    elif query == "🎧 Новинки": query = "Новинки музыки 2026"

    status_msg = await update.message.reply_text("🔍 Поиск... ⏳")
    
    tracks = []
    try:
        with yt_dlp.YoutubeDL(YDL_OPTS_SEARCH) as ydl:
            res = ydl.extract_info(f"ytsearch5:{query}", download=False)
            entries = res.get('entries', []) if res else []
            for entry in entries[:5]:
                tracks.append({'id': entry['id'], 'title': entry['title'], 'url': f"https://www.youtube.com/watch?v={entry['id']}"})
    except: pass

    if not tracks:
        await status_msg.edit_text("❌ К сожалению, ничего не найдено. Попробуйте другой запрос!")
        return

    search_cache[user_id] = tracks
    keyboard = [[InlineKeyboardButton(f"🎵 {tr['title'][:40]}", callback_data=f"dl_{i}")] for i, tr in enumerate(tracks)]
    await status_msg.delete()
    await update.message.reply_text("🎧 Выберите вариант из списка: 👇", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not query.data.startswith("dl_"): return
    
    idx = int(query.data.split("_")[1])
    tracks = search_cache.get(query.from_user.id)
    if not tracks or idx >= len(tracks): return

    track = tracks[idx]
    status_msg = await query.message.reply_text(f"⏳ Скачиваю: {track['title']}... 🚀")

    for f in glob.glob("temp_audio.*"): 
        try: os.remove(f)
        except: pass

    try:
        with yt_dlp.YoutubeDL(YDL_OPTS_DOWNLOAD) as ydl:
            ydl.extract_info(track['url'], download=True)
            file_path = glob.glob("temp_audio.mp3")[0]
            with open(file_path, 'rb') as f:
                await query.message.reply_audio(audio=f, title=track['title'], thumbnail=f"https://img.youtube.com/vi/{track['id']}/hqdefault.jpg")
            os.remove(file_path)
            await status_msg.delete()
    except:
        await status_msg.edit_text("❌ Ошибка при загрузке. Попробуйте снова.")

if __name__ == "__main__":
    Thread(target=run).start()
    bot = ApplicationBuilder().token(TOKEN).build()
    bot.add_handler(CommandHandler("start", start_command))
    bot.add_handler(CallbackQueryHandler(button_callback))
    bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    bot.run_polling()
