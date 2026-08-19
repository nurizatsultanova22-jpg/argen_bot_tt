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

# Yandex Music же жалпы издөө (ката бербейт)
YDL_OPTIONS = {
    'format': 'best',
    'quiet': True,
    'no_warnings': True,
    'nocheckcertificate': True,
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = ReplyKeyboardMarkup([["🔥 Популярное", "🎧 Новинки"]], resize_keyboard=True)
    await update.message.reply_text("Привет! Напиши название песни, я быстро найду трек и видео! 🎬", reply_markup=reply_markup)

async def search_and_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    if query in ["🔥 Популярное", "🎧 Новинки"]:
        query = "Хиты 2026"
    
    status = await update.message.reply_text("🔍 Ищу музыку...")
    
    try:
        # YouTube ордуна Yandex Music же альтернативалуу булактан издөө (Sign in катасы чыкпайт)
        with yt_dlp.YoutubeDL({'default_search': 'yandexmusicsearch5', **YDL_OPTIONS}) as ydl:
            results = ydl.extract_info(f"yandexmusicsearch5:{query}", download=False)
            entries = results.get('entries', [])
        
        # Эгер Yandex таппаса, жалпы web аркылуу издейбиз
        if not entries:
            with yt_dlp.YoutubeDL({'default_search': 'auto', **YDL_OPTIONS}) as ydl:
                results = ydl.extract_info(f"auto:{query}", download=False)
                entries = results.get('entries', [])[:5]

        if not entries:
            await status.edit_text("❌ Ничего не найдено.")
            return

        keyboard = []
        for i, entry in enumerate(entries):
            title = entry.get('title', 'Трек')
            keyboard.append([InlineKeyboardButton(f"🎵 {title[:35]}", callback_data=f"play_{i}")])
        
        context.user_data['results'] = entries
        await status.delete()
        await update.message.reply_text("Выберите вариант:", reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        await status.edit_text("❌ Ошибка поиска. Попробуйте другой запрос.")

async def play_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    idx = int(query.data.split("_")[1])
    entry = context.user_data['results'][idx]
    
    status = await query.message.reply_text("⏳ Загружаю...")
    
    try:
        url = entry.get('webpage_url') or entry.get('url')
        with yt_dlp.YoutubeDL({'outtmpl': 'media.mp4', **YDL_OPTIONS}) as ydl:
            ydl.download([url])
        
        if os.path.exists('media.mp4'):
            await query.message.reply_video(video=open('media.mp4', 'rb'), caption=entry.get('title', ''))
            os.remove('media.mp4')
        elif os.path.exists('media.mkv'):
            await query.message.reply_video(video=open('media.mkv', 'rb'), caption=entry.get('title', ''))
            os.remove('media.mkv')
        
        await status.delete()
    except:
        await status.edit_text("❌ Ошибка при скачивании файла.")

if __name__ == "__main__":
    Thread(target=run).start()
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(play_video))
    app_bot.add_handler(MessageHandler(filters.TEXT, search_and_send))
    app_bot.run_polling()
