import os
import random
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, CommandHandler, filters, ContextTypes
import yt_dlp
from flask import Flask
from threading import Thread

TELEGRAM_BOT_TOKEN = "8817519388:AAH05Kz22gJ5bey4m-9p0TwiSmme7WGmnz4"
ADMIN_USERNAME = "@Argen_70"

app_web = Flask('')
@app_web.route('/')
def home(): return "Бот работает!"
def run_web(): app_web.run(host='0.0.0.0', port=10000)

users_set = set()
saved_broadcast_content = None
user_languages = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    users_set.add(user_id)
    
    keyboard = [
        [
            InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
            InlineKeyboardButton("🇰🇬 Кыргызча", callback_data="lang_kg"),
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        f"🎧 Привет! Какую песню желаешь?\n\n"
        f"🌍 Выберите язык для поиска треков:\n\n"
        f"👑 Мой админ: {ADMIN_USERNAME}"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)

async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    
    lang_name = "Русский"
    if query.data == "lang_kg": lang_name = "Кыргызча"
    elif query.data == "lang_en": lang_name = "English"
    
    user_languages[user_id] = lang_name
    await query.edit_message_text(
        text=f"✅ Язык выбран: **{lang_name}**.\n\n🔍 Теперь отправьте название трека, саундтрека или напишите **найти [название]**!\n\n👑 Мой админ: {ADMIN_USERNAME}",
        parse_mode="Markdown"
    )

async def download_and_send_audio(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
    chat_id = update.effective_chat.id
    users_set.add(chat_id)
    
    ydl_opts = {
        'format': 'bestaudio',
        'noplaylist': True,
        'default_search': 'scsearch1',
        'quiet': True,
        'outtmpl': 'song.mp3',
    }
    
    status_msg = await context.bot.send_message(chat_id=chat_id, text="⏳ Подаждите, ищу трек... [3 сек]")
    await asyncio.sleep(1)
    try: await context.bot.edit_message_text(chat_id=chat_id, message_id=status_msg.message_id, text="⏳ Подаждите, ищу трек... [2 сек]")
    except: pass
    await asyncio.sleep(1)
    try: await context.bot.edit_message_text(chat_id=chat_id, message_id=status_msg.message_id, text="⏳ Подаждите, ищу трек... [1 сек]")
    except: pass
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"scsearch1:{query}", download=True)
            if 'entries' in info:
                info = info['entries'][0]
            
            title = info.get('title', 'Музыка')
        
        keyboard = [
            [
                InlineKeyboardButton("❤️ Огонь 🔥", callback_data="like_fire"),
                InlineKeyboardButton("💪 Мощь 🚀", callback_data="like_power")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        caption_text = f"🎵 {title}\n\n✨ Мотивирующий трек!\n👑 Мой админ: {ADMIN_USERNAME}"
        
        with open("song.mp3", 'rb') as audio:
            await context.bot.send_audio(
                chat_id=chat_id, 
                audio=audio, 
                title=title, 
                caption=caption_text,
                reply_markup=reply_markup
            )
        
        await context.bot.delete_message(chat_id=chat_id, message_id=status_msg.message_id)
        if os.path.exists("song.mp3"): os.remove("song.mp3")
            
    except Exception as e:
        await context.bot.edit_message_text(
            chat_id=chat_id, 
            message_id=status_msg.message_id, 
            text=f"❌ Трек не найден!\n👑 Мой админ: {ADMIN_USERNAME}"
        )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data.startswith("lang_"):
        await language_callback(update, context)
        return

    await query.answer()
    caption = query.message.caption or ""
    if query.data == "like_fire":
        try: await query.edit_message_caption(caption=caption + "\n\n🔥 Оценка: Полный огонь!", reply_markup=query.message.reply_markup)
        except: pass
    elif query.data == "like_power":
        try: await query.edit_message_caption(caption=caption + "\n\n💪 Оценка: Настоящая мощь!", reply_markup=query.message.reply_markup)
        except: pass

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global saved_broadcast_content
    user_id = update.effective_user.id
    users_set.add(user_id)
    
    if not update.message:
        return

    text = update.message.text.strip() if update.message.text else ""
    
    # Эгер админ "+" жиберсе (Рассылка баардык катталгандарга)
    if text == "+":
        if saved_broadcast_content:
            success_count = 0
            for uid in users_set:
                try:
                    if update.message.photo:
                        await context.bot.send_photo(chat_id=uid, photo=update.message.photo[-1].file_id, caption=update.message.caption)
                    else:
                        await context.bot.send_message(chat_id=uid, text=saved_broadcast_content)
                    success_count += 1
                except:
                    pass
            await update.message.reply_text(f"✅ Рассылка отправлена {success_count} пользователям!")
        else:
            await update.message.reply_text("⚠️ Сначала отправьте контент, а затем '+' для рассылки.")
        return

    # Админ контент жөнөтсө сактап калат (Башка колдонуучуларга Х чыгат)
    # Админди аныктоо үчүн юзернеймди текшеребиз же өзүңүз экениңизди билебиз
    is_admin = update.effective_user.username == "Argen_70" or update.effective_user.id == list(users_set)[0] # же негизги админ
    
    if update.message.photo or (text and not text.lower().startswith("найти") and not text.lower().startswith("трек") and len(text) > 20):
        saved_broadcast_content = text if text else (update.message.caption or "Контент")
        await update.message.reply_text("📥 Контент сохранен в базу! Нажмите **+** чтобы показать всем.")
        return

    # Музыка издөө (найти же трек же каалаган сөз)
    query_text = ""
    if text.lower().startswith("найти"):
        query_text = text[5:].strip()
    elif text.lower().startswith("трек"):
        query_text = text[4:].strip()
    else:
        query_text = text

    if query_text:
        await download_and_send_audio(update, context, query_text)
    else:
        await update.message.reply_text("❌")

if __name__ == "__main__":
    t = Thread(target=run_web); t.start()
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), handle_message))
    app.run_polling()
