import os
import yt_dlp
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes
from threading import Thread
from flask import Flask

TOKEN = "8558649634:AAHEqz0qKwSg46pcqme0D84pLsdAmVIe8p8"

app = Flask('')
@app.route('/')
def home(): return "Бот работает! 🚀"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))

# Эң күчтүү жөндөө (YouTube бөгөттөсө да иштейт)
YDL_OPTIONS = {
    'format': 'best',
    'quiet': True,
    'no_warnings': True,
    'nocheckcertificate': True,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = ReplyKeyboardMarkup([["🔥 Популярное", "🎧 Новинки"]], resize_keyboard=True)
    await update.message.reply_text("Привет! Напиши название песни или видео, я найду его!", reply_markup=reply_markup)

async def search_and_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    if query in ["🔥 Популярное", "🎧 Новинки"]:
        query = "Top music 2026"
    
    status = await update.message.reply_text("🔍 Ищу...")
    
    try:
        # YouTube издөө
        with yt_dlp.YoutubeDL({'default_search': 'ytsearch5', **YDL_OPTIONS}) as ydl:
            results = ydl.extract_info(f"ytsearch5:{query}", download=False)
            entries = results.get('entries', [])
        
        if not entries:
            await status.edit_text("❌ Ничего не найдено.")
            return

        keyboard = []
        for i, entry in enumerate(entries):
            keyboard.append([InlineKeyboardButton(f"🎬 {entry['title'][:35]}", callback_data=f"play_{i}")])
        
        context.user_data['results'] = entries
        await status.delete()
        await update.message.reply_text("Вот что я нашел:", reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        await status.edit_text(f"❌ Ошибка поиска: {str(e)[:50]}")

async def play_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    idx = int(query.data.split("_")[1])
    entry = context.user_data['results'][idx]
    
    status = await query.message.reply_text("⏳ Загружаю...")
    
    try:
        # Видео жүктөө
        with yt_dlp.YoutubeDL({'outtmpl': 'vid.mp4', **YDL_OPTIONS}) as ydl:
            ydl.download([entry['webpage_url']])
        
        await query.message.reply_video(video=open('vid.mp4', 'rb'), caption=entry['title'])
        os.remove('vid.mp4')
        await status.delete()
    except:
        await status.edit_text("❌ Ошибка при скачивании видео. Попробуйте снова.")

if __name__ == "__main__":
    Thread(target=run).start()
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(play_video))
    app_bot.add_handler(MessageHandler(filters.TEXT, search_and_send))
    app_bot.run_polling()
