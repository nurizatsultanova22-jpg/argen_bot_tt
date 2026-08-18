import os
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, CommandHandler, filters, ContextTypes
import yt_dlp
from flask import Flask
from threading import Thread

TELEGRAM_BOT_TOKEN = "8817519388:AAH05Kz22gJ5bey4m-9p0TwiSmme7WGmnz4"

# ... (web server бөлүгү өзгөрүүсүз) ...
app_web = Flask('')
@app_web.route('/')
def home(): return "Бот работает!"
def run_web(): app_web.run(host='0.0.0.0', port=10000)

user_games = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привет! Я твой музыкальный друг! 🎶\nПиши 'найти [песня]' или 'игра' для веселья! 🚀")

async def download_and_send_audio(chat_id, query, context):
    ydl_opts = {
        'format': 'bestaudio/best', 'noplaylist': True, 'default_search': 'ytsearch1',
        'quiet': True, 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '128'}],
        'outtmpl': 'song.mp3',
    }
    
    status_msg = await context.bot.send_message(chat_id=chat_id, text=f"🔍 Ищу твой трек... Погоди капельку! 🏃‍♂️💨")
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=True)
            if 'entries' in info: info = info['entries'][0]
            title = info.get('title', 'Музыка')
        
        keyboard = [[InlineKeyboardButton("❤️", callback_data="like_heart"), InlineKeyboardButton("💔", callback_data="like_broken")]]
        
        with open("song.mp3", 'rb') as audio:
            await context.bot.send_audio(chat_id=chat_id, audio=audio, title=title, 
                                       caption=f"🎧 Нашел! {title}\n\nНадеюсь, тебе понравится! 💫", 
                                       reply_markup=InlineKeyboardMarkup(keyboard))
        
        await context.bot.delete_message(chat_id=chat_id, message_id=status_msg.message_id)
        if os.path.exists("song.mp3"): os.remove("song.mp3")
    except:
        await context.bot.edit_message_text(chat_id=chat_id, message_id=status_msg.message_id, text="😢 Ой, не нашел... Давай попробуем что-то другое? 🥺")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "like_heart":
        await query.edit_message_caption(caption=query.message.caption + "\n\n❤️ Ого, крутой вкус! Рад, что понравилось! 😍")
    elif query.data == "like_broken":
        await query.edit_message_caption(caption=query.message.caption + "\n\n💔 Жаль... Буду искать лучше в следующий раз! 😔")

async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_games[chat_id] = random.randint(1, 10)
    await update.message.reply_text("🎲 Давай сыграем! Я загадал число от 1 до 10. Угадаешь? 🤔")

async def check_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in user_games:
        try:
            guess = int(update.message.text)
            if guess == user_games[chat_id]:
                await update.message.reply_text("🏆 Ура! Ты гений, угадал! 🎉🥳")
                del user_games[chat_id]
            else:
                await update.message.reply_text("🙊 Не-а! Попробуй еще разок, я верю в тебя! 💪")
        except: pass

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text.lower().startswith("найти"):
        await download_and_send_audio(update.effective_chat.id, text[5:].strip(), context)
    elif text.lower() == "игра":
        await start_game(update, context)
    elif text.isdigit():
        await check_guess(update, context)

if __name__ == "__main__":
    t = Thread(target=run_web); t.start()
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
