import os
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes
from threading import Thread
from flask import Flask
import yt_dlp

TOKEN = "8558649634:AAHEqz0qKwSg46pcqme0D84pLsdAmVIe8p8"
ADMIN_USER = "@Argen_70"

app = Flask('')
@app.route('/')
def home(): return "Бот работает идеально!"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))

song_database = {}
search_cache = {}

POPULAR_TRACKS = [
    "Bakr - Самая близкая",
    "Miyagi & Эндшпиль - Minor",
    "Macan - Asphalt 8",
    "Xcho - Воспоминания",
    "ALHAM - Hikayam"
]

# YouTube бөгөтүн айланып өтүү үчүн коопсуз жөндөөлөр
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'extractor_args': {'youtube': {'player_client': ['android', 'web']}}
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🎧 Добро пожаловать в музыкальный бот!\n\n"
        "🚀 Просто отправь название трека или текст, и я сразу найду его!\n"
        "💾 Все найденные треки сохраняются в базу с обложками!\n\n"
        f"👑 Администратор: {ADMIN_USER}"
    )
    reply_markup = ReplyKeyboardMarkup([["🔥 Популярные треки"]], resize_keyboard=True)
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response_text = "🔥 **Самые популярные треки:**\n\n"
    keyboard = []
    row = []
    user_id = update.effective_user.id
    entries = []
    
    for i, track_name in enumerate(POPULAR_TRACKS, 1):
        response_text += f"🎵 **{i}. {track_name}**\n"
        try:
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                res = ydl.extract_info(f"ytsearch1:{track_name}", download=False)
                for entry in res.get('entries', []):
                    entries.append({
                        'title': entry.get('title', track_name),
                        'url': entry.get('url'),
                        'thumbnail': entry.get('thumbnail')
                    })
        except:
            pass
        row.append(InlineKeyboardButton(str(i), callback_data=f"select_{i-1}"))
    
    if entries:
        search_cache[user_id] = entries
        keyboard.append(row)
        await update.message.reply_text(response_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Не удалось загрузить топ треков.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = (update.message.text or "").strip()
    
    if not text:
        return

    if text == "🔥 Популярные треки":
        await top_command(update, context)
        return

    query = text
    if text.lower().startswith("трек "):
        query = text[5:].strip()
    elif text.lower().startswith("найти "):
        query = text[6:].strip()

    query_lower = query.lower()

    if query_lower in song_database:
        saved_entry = song_database[query_lower]
        try:
            caption_text = f"🎵 *{saved_entry['title']}*\n\n✨ Приятного прослушивания!\n👑 Администратор: {ADMIN_USER}"
            if saved_entry.get('thumbnail'):
                await context.bot.send_photo(chat_id=update.effective_chat.id, photo=saved_entry['thumbnail'], caption=caption_text, parse_mode="Markdown")
            await context.bot.send_audio(chat_id=update.effective_chat.id, audio=saved_entry['url'], title=saved_entry['title'])
            return
        except:
            pass

    status_msg = await update.message.reply_text("⚡ Ищу трек... 🔍")
    
    entries = []
    try:
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            res = ydl.extract_info(f"ytsearch5:{query}", download=False)
            for entry in res.get('entries', []):
                entries.append({
                    'title': entry.get('title', 'Музыка'),
                    'url': entry.get('url'),
                    'thumbnail': entry.get('thumbnail')
                })
    except Exception as e:
        pass

    if not entries:
        await status_msg.edit_text("❌ Трек не найден. Попробуйте написать по-другому.")
        return

    search_cache[user.id] = entries
    
    first_entry = entries[0]
    response_text = f"🎧 Запрос: *{query}*\n\n🎵 **Самые лучшие результаты:**\n\n"
    keyboard = []
    row = []
    for i, entry in enumerate(entries[:5], 1):
        title = entry.get('title', 'Музыка')
        response_text += f"🔹 **{i}. {title}**\n"
        row.append(InlineKeyboardButton(str(i), callback_data=f"select_{i-1}"))
    keyboard.append(row)

    await status_msg.delete()
    
    if first_entry.get('thumbnail'):
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=first_entry['thumbnail'],
            caption=response_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(response_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if query.data.startswith("select_"):
        index = int(query.data.split("_")[1])
        entries = search_cache.get(user_id)
        if not entries or index >= len(entries):
            await query.message.edit_text("⚠️ Срок поиска истек. Отправьте запрос заново.")
            return

        selected = entries[index]
        url = selected.get('url')
        title = selected.get('title', 'Музыка')
        thumbnail = selected.get('thumbnail')
        
        song_database[title.lower()] = {'title': title, 'url': url, 'thumbnail': thumbnail}

        status_msg = await query.message.reply_text(f"⚡ Отправляю: *{title}* ⏳", parse_mode="Markdown")

        try:
            caption_text = f"🎵 *{title}*\n\n✨ Приятного прослушивания!\n👑 Администратор: {ADMIN_USER}"
            
            if thumbnail:
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=thumbnail,
                    caption=caption_text,
                    parse_mode="Markdown"
                )

            await context.bot.send_audio(
                chat_id=query.message.chat_id,
                audio=url,
                title=title
            )
            await status_msg.delete()
        except Exception as e:
            await status_msg.edit_text("❌ Не удалось отправить аудиофайл.")

if __name__ == "__main__":
    Thread(target=run).start()
    bot = ApplicationBuilder().token(TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("top", top_command))
    bot.add_handler(CallbackQueryHandler(button_callback))
    bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    bot.run_polling()
