import os
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, CommandHandler, filters, ContextTypes
import yt_dlp
from flask import Flask
from threading import Thread

TELEGRAM_BOT_TOKEN = "8817519388:AAH05Kz22gJ5bey4m-9p0TwiSmme7WGmnz4"

app_web = Flask('')
@app_web.route('/')
def home(): return "Бот работает!"
def run_web(): app_web.run(host='0.0.0.0', port=10000)

user_games = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    welcome_text = (
        f"🎧 Привет, {user_name}! Я твой музыкальный бот.\n\n"
        "🔍 Чтобы найти песню, просто отправь её название или напиши: **найти [название]**\n"
        "🎮 А если хочешь отдохнуть, напиши **игра**!"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def download_and_send_audio(chat_id, query, context):
    ydl_opts = {
        'format': 'bestaudio',
        'noplaylist': True,
        'default_search': 'scsearch1',
        'quiet': True,
        'outtmpl': 'song.mp3',
    }
    
    status_msg = await context.bot.send_message(chat_id=chat_id, text=f"⏳ Ищу трек **{query}**, подождите немного...", parse_mode="Markdown")
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"scsearch1:{query}", download=True)
            if 'entries' in info:
                info = info['entries'][0]
            
            title = info.get('title', 'Музыка')
        
        keyboard = [
            [
                InlineKeyboardButton("❤️ Ужас как нравится", callback_data="like_heart"),
                InlineKeyboardButton("👎 Так себе", callback_data="like_broken")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        with open("song.mp3", 'rb') as audio:
            await context.bot.send_audio(
                chat_id=chat_id, 
                audio=audio, 
                title=title, 
                caption=f"🎵 **{title}**\n\n✨ Приятного прослушивания!", 
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
        
        await context.bot.delete_message(chat_id=chat_id, message_id=status_msg.message_id)
        if os.path.exists("song.mp3"): os.remove("song.mp3")
            
    except Exception as e:
        await context.bot.edit_message_text(
            chat_id=chat_id, 
            message_id=status_msg.message_id, 
            text="❌ К сожалению, по вашему запросу ничего не найдено. Попробуйте написать точнее!"
        )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    caption = query.message.caption or ""
    if query.data == "like_heart":
        try: await query.edit_message_caption(caption=caption + "\n\n❤️ Вы оценили трек положительно!", reply_markup=query.message.reply_markup)
        except: pass
    elif query.data == "like_broken":
        try: await query.edit_message_caption(caption=caption + "\n\n👎 Вы оценили трек отрицательно.", reply_markup=query.message.reply_markup)
        except: pass

async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_games[chat_id] = random.randint(1, 10)
    await update.message.reply_text("🎲 Я загадал число от 1 до 10. Попробуй отгадать, отправь цифру в чат!")

async def check_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in user_games:
        try:
            guess = int(update.message.text)
            if guess == user_games[chat_id]:
                await update.message.reply_text("🎉 Поздравляю! Вы угадали число!")
                del user_games[chat_id]
            else:
                await update.message.reply_text("❌ Неверно! Попробуйте еще раз.")
        except: pass

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    if text.lower().startswith("найти"):
        query = text[5:].strip()
        if query:
            await download_and_send_audio(update.effective_chat.id, query, context)
        else:
            await update.message.reply_text("⚠️ Напишите название после слова найти.")
    elif text.lower() == "игра":
        await start_game(update, context)
    elif text.isdigit():
        await check_guess(update, context)
    else:
        await download_and_send_audio(update.effective_chat.id, text, context)

if __name__ == "__main__":
    t = Thread(target=run_web); t.start()
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
