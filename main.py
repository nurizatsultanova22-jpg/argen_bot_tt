import os
import requests
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes
from threading import Thread
from flask import Flask

TOKEN = "8558649634:AAHEqz0qKwSg46pcqme0D84pLsdAmVIe8p8"

app = Flask('')
@app.route('/')
def home(): return "Бот работает! 🚀"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))

# Бир нече ишенимдүү Piped API серверлери
PIPED_INSTANCES = [
    "https://pipedapi.kavin.rocks",
    "https://pipedapi.in.projectsegfault.net",
    "https://api-piped.mha.fi"
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = ReplyKeyboardMarkup([["🔥 Популярное", "🎧 Новинки"]], resize_keyboard=True)
    await update.message.reply_text("Привет! Напиши название песни, я найду через Piped! 🎬", reply_markup=reply_markup)

async def search_and_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    if not query: return
    
    if query in ["🔥 Популярное", "🎧 Новинки"]:
        query = "Top music hits 2026"
    
    status = await update.message.reply_text("🔍 Ищу трек...")
    
    data = None
    # Иштеп жаткан серверди табуу
    for api in PIPED_INSTANCES:
        try:
            response = requests.get(f"{api}/search?q={query}&filter=videos", timeout=5)
            if response.status_code == 200:
                data = response.json()
                break
        except:
            continue
            
    if not data or not data.get('items'):
        await status.edit_text("❌ Ничего не найдено. Попробуйте другой запрос.")
        return

    items = data.get('items', [])[:5]
    keyboard = []
    tracks = []
    for item in items:
        title = item.get('title', 'Видео')
        url_id = item.get('url', '').replace('/watch?v=', '')
        if url_id:
            keyboard.append([InlineKeyboardButton(f"🎬 {title[:35]}", callback_data=f"dl_{url_id}")])
            tracks.append({'title': title, 'id': url_id})
    
    if not tracks:
        await status.edit_text("❌ Ошибка обработки результатов.")
        return

    context.user_data['results'] = tracks
    await status.delete()
    await update.message.reply_text("Выберите вариант:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not query.data.startswith("dl_"): return
    
    video_id = query.data.split("_")[1]
    status = await query.message.reply_text("⏳ Загружаю видео...")

    stream_data = None
    for api in PIPED_INSTANCES:
        try:
            res = requests.get(f"{api}/streams/{video_id}", timeout=5)
            if res.status_code == 200:
                stream_data = res.json()
                break
        except:
            continue

    if not stream_data:
        await status.edit_text("❌ Не удалось получить видеопоток.")
        return

    video_streams = stream_data.get('videoStreams', [])
    mp4_url = None
    for s in video_streams:
        if s.get('format') == 'MPEG_4' and s.get('url'):
            mp4_url = s.get('url')
            break
    
    if not mp4_url and video_streams:
        mp4_url = video_streams[0].get('url')

    if mp4_url:
        try:
            await query.message.reply_video(video=mp4_url, caption="Готово! 🚀")
            await status.delete()
        except:
            await status.edit_text("❌ Ошибка при отправке файла в Telegram.")
    else:
            await status.edit_text("❌ Не найдена прямая ссылка на видео.")

if __name__ == "__main__":
    Thread(target=run).start()
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(button_callback))
    app_bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), search_and_send))
    app_bot.run_polling()
