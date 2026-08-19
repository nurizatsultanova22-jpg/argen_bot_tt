import os
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

# Видео форматын алуу үчүн жөндөө (ffmpeg керек эмес, ката чыкпайт)
YDL_OPTS_VIDEO = {
    'format': 'best[ext=mp4]/best',
    'outtmpl': 'temp_video.mp4',
    'quiet': True,
    'noplaylist': True,
    'nocheckcertificate': True
}

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["🔥 Популярное", "🎧 Новинки"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Привет! Напиши название, я пришлю видео-трек! 🎬", reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    query = update.message.text
    if not query: return
    
    if query == "🔥 Популярное": query = "Хиты 2026"
    elif query == "🎧 Новинки": query = "Новинки музыки"

    status_msg = await update.message.reply_text("🔍 Ищу видео... ⏳")
    
    tracks = []
    try:
        with yt_dlp.YoutubeDL({'default_search': 'ytsearch5', 'quiet': True}) as ydl:
            res = ydl.extract_info(f"ytsearch5:{query}", download=False)
            for entry in res.get('entries', []):
                tracks.append({'id': entry['id'], 'title': entry['title']})
    except: pass

    if not tracks:
        await status_msg.edit_text("❌ Ничего не найдено.")
        return

    search_cache[user_id] = tracks
    keyboard = [[InlineKeyboardButton(f"🎬 {tr['title'][:40]}", callback_data=f"dl_{i}")] for i, tr in enumerate(tracks)]
    await status_msg.delete()
    await update.message.reply_text("Выберите видео для отправки: 👇", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not query.data.startswith("dl_"): return
    
    idx = int(query.data.split("_")[1])
    tracks = search_cache.get(query.from_user.id)
    track = tracks[idx]

    status_msg = await query.message.reply_text(f"⏳ Отправляю видео: {track['title']}...")

    try:
        # Видео файлды жүктөп алуу
        with yt_dlp.YoutubeDL(YDL_OPTS_VIDEO) as ydl:
            ydl.download([f"https://www.youtube.com/watch?v={track['id']}"])
        
        # Видео файлды Telegram'га жөнөтүү
        with open('temp_video.mp4', 'rb') as f:
            await query.message.reply_video(video=f, caption=track['title'])
        
        os.remove('temp_video.mp4')
        await status_msg.delete()
    except Exception as e:
        await status_msg.edit_text(f"❌ Ошибка отправки видео.")

if __name__ == "__main__":
    Thread(target=run).start()
    bot = ApplicationBuilder().token(TOKEN).build()
    bot.add_handler(CommandHandler("start", start_command))
    bot.add_handler(CallbackQueryHandler(button_callback))
    bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    bot.run_polling()
