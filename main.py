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

# Piped публичный API сыртынан издөө үчүн
PIPED_API = "https://pipedapi.kavin.rocks"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = ReplyKeyboardMarkup([["🔥 Популярное", "🎧 Новинки"]], resize_keyboard=True)
    await update.message.reply_text("Привет! Напиши название, я найду видео через Piped! 🎬", reply_markup=reply_markup)

async def search_and_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    if not query: return
    
    if query in ["🔥 Популярное", "🎧 Новинки"]:
        query = "Top music hits 2026"
    
    status = await update.message.reply_text("🔍 Ищу через Piped API...")
    
    try:
        response = requests.get(f"{PIPED_API}/search?q={query}&filter=videos", timeout=10)
        data = response.json()
        items = data.get('items', [])[:5]
        
        if not items:
            await status.edit_text("❌ Ничего не найдено.")
            return

        keyboard = []
        tracks = []
        for item in items:
            title = item.get('title', 'Видео')
            # urlId же url аркылуу видео ID алуу
            url_id = item.get('url', '').replace('/watch?v=', '')
            if url_id:
                keyboard.append([InlineKeyboardButton(f"🎬 {title[:35]}", callback_data=f"dl_{url_id}")])
                tracks.append({'title': title, 'id': url_id})
        
        context.user_data['results'] = tracks
        await status.delete()
        await update.message.reply_text("Выберите видео:", reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        await status.edit_text("❌ Ошибка поиска.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not query.data.startswith("dl_"): return
    
    video_id = query.data.split("_")[1]
    status = await query.message.reply_text("⏳ Получаю прямую ссылку на видео...")

    try:
        # Piped аркылуу видеонун түз шилтемесин алуу
        res = requests.get(f"{PIPED_API}/streams/{video_id}", timeout=10)
        stream_data = res.json()
        
        video_streams = stream_data.get('videoStreams', [])
        # Эң жакшы сапаттагы mp4 шилтеmesini табуу
        mp4_url = None
        for s in video_streams:
            if s.get('format') == 'MPEG_4' and s.get('url'):
                mp4_url = s.get('url')
                break
        
        if not mp4_url and video_streams:
            mp4_url = video_streams[0].get('url')

        if mp4_url:
            await query.message.reply_video(video=mp4_url, caption="Готово! 🚀")
            await status.delete()
        else:
            await status.edit_text("❌ Не удалось найти прямую ссылку на видео.")
    except Exception as e:
        await status.edit_text("❌ Ошибка при отправке видео.")

if __name__ == "__main__":
    Thread(target=run).start()
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(button_callback))
    app_bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), search_and_send))
    app_bot.run_polling()
