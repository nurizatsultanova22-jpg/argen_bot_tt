import os
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🎧 Добро пожаловать в музыкальный бот!\n\n"
        "🚀 В группах и чатах бот ищет музыку **только через команду /трек [название]**.\n"
        "💾 Все найденные треки сохраняются в базу с обложками!\n\n"
        "🔥 Команды:\n"
        "• `/трек Название песни` — Поиск трека\n"
        "• `/top` — Популярные треки\n\n"
        f"👑 Администратор: {ADMIN_USER}"
    )
    keyboard = [[InlineKeyboardButton("🔥 Популярные треки (Топ)", callback_data="show_top")]]
    await update.message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response_text = "🔥 **Самые популярные треки:**\n\n"
    keyboard = []
    row = []
    user_id = update.effective_user.id
    entries = []
    
    ydl_opts = {'format': 'bestaudio', 'default_search': 'scsearch1', 'quiet': True}
    for i, track_name in enumerate(POPULAR_TRACKS, 1):
        response_text += f"🎵 **{i}. {track_name}**\n"
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                res = ydl.extract_info(f"scsearch1:{track_name}", download=False)
                for entry in res.get('entries', []):
                    entries.append({
                        'title': entry.get('title', track_name),
                        'url': entry.get('webpage_url') or entry.get('url'),
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

async def track_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args
    
    if not args:
        await update.message.reply_text("⚠️ Пожалуйста, укажите название после команды. Пример:\n`/трек Bakr`", parse_mode="Markdown")
        return

    query = " ".join(args).strip()
    query_lower = query.lower()

    # 1. Базадан издөө
    if query_lower in song_database:
        saved_entry = song_database[query_lower]
        status_msg = await update.message.reply_text(f"⚡ Найдено в базе! Загружаю: *{saved_entry['title']}* ⏳", parse_mode="Markdown")
        try:
            ydl_opts = {'format': 'bestaudio', 'quiet': True, 'outtmpl': 'song.mp3', 'noplaylist': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([saved_entry['url']])

            caption_text = f"🎵 *{saved_entry['title']}*\n\n✨ Приятного прослушивания!\n👑 Администратор: {ADMIN_USER}"
            
            # Сүрөтү бар болсо сүрөтү менен, болбосо жөнөкөй аудио жөнөтөбүз
            if saved_entry.get('thumbnail'):
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=saved_entry['thumbnail'],
                    caption=caption_text,
                    parse_mode="Markdown"
                )
            
            with open("song.mp3", 'rb') as audio:
                await context.bot.send_audio(chat_id=update.effective_chat.id, audio=audio, title=saved_entry['title'])
            
            await status_msg.delete()
            if os.path.exists("song.mp3"): os.remove("song.mp3")
            return
        except:
            pass

    status_msg = await update.message.reply_text("⚡ Ищу трек по базам данных... 🔍")
    
    ydl_opts = {'format': 'bestaudio', 'default_search': 'scsearch5', 'quiet': True}
    entries = []
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            res = ydl.extract_info(f"scsearch5:{query}", download=False)
            for entry in res.get('entries', []):
                entries.append({
                    'title': entry.get('title', 'Музыка'),
                    'url': entry.get('webpage_url') or entry.get('url'),
                    'thumbnail': entry.get('thumbnail')
                })
    except:
        pass

    if not entries:
        await status_msg.edit_text("❌ Трек или текст не найден. Попробуйте написать по-другому.")
        return

    search_cache[user.id] = entries
    
    # 2. Чоң жана кооз көрүнүш
    response_text = f"🎧 Запрос: *{query}*\n\n🎵 **Самые лучшие результаты:**\n\n"
    keyboard = []
    row = []
    for i, entry in enumerate(entries[:5], 1):
        title = entry.get('title', 'Музыка')
        response_text += f"🔹 **{i}. {title}**\n"
        row.append(InlineKeyboardButton(str(i), callback_data=f"select_{i-1}"))
    keyboard.append(row)

    await status_msg.edit_text(response_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if query.data == "show_top":
        await top_command(update, context)
        return
        
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
        
        # Базага сактоо
        song_database[title.lower()] = {'title': title, 'url': url, 'thumbnail': thumbnail}

        status_msg = await query.message.reply_text(f"📥 Загружаю трек: *{title}* ⏳", parse_mode="Markdown")

        try:
            ydl_opts = {
                'format': 'bestaudio',
                'quiet': True,
                'outtmpl': 'song.mp3',
                'noplaylist': True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            caption_text = f"🎵 *{title}*\n\n✨ Приятного прослушивания!\n👑 Администратор: {ADMIN_USER}"
            
            # Сүрөтү менен кошо жөнөтүү
            if thumbnail:
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=thumbnail,
                    caption=caption_text,
                    parse_mode="Markdown"
                )

            with open("song.mp3", 'rb') as audio:
                await context.bot.send_audio(
                    chat_id=query.message.chat_id,
                    audio=audio,
                    title=title
                )
            await status_msg.delete()
            if os.path.exists("song.mp3"): os.remove("song.mp3")
        except:
            await status_msg.edit_text("❌ Ошибка при скачивании файла.")

if __name__ == "__main__":
    Thread(target=run).start()
    bot = ApplicationBuilder().token(TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("top", top_command))
    bot.add_handler(CommandHandler("трек", track_command))
    bot.add_handler(CommandHandler("track", track_command))
    bot.add_handler(CallbackQueryHandler(button_callback))
    # Жөнөкөй тексттерге жооп бербейт, чаттарды тоспойт
    bot.run_polling()
