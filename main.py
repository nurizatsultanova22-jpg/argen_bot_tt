import os
import urllib.parse
import urllib.request
import json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes
from threading import Thread
from flask import Flask

TOKEN = "8558649634:AAHEqz0qKwSg46pcqme0D84pLsdAmVIe8p8"
ADMIN_USER = "@Argen_70"

app = Flask('')
@app.route('/')
def home(): return "Бот работает идеально!"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))

search_cache = {}

POPULAR_TRACKS = [
    "Bakr",
    "Miyagi",
    "Macan",
    "Xcho",
    "ALHAM"
]

def search_tracks(query):
    results = []
    try:
        encoded_q = urllib.parse.quote(query)
        url = f"https://api.deezer.com/search?q={encoded_q}&limit=5"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            for item in data.get('data', []):
                artist = item.get('artist', {}).get('name', '')
                title = item.get('title', '')
                track_name = f"{artist} - {title}"
                preview_url = item.get('preview')
                album = item.get('album', {})
                artwork = album.get('cover_xl') or album.get('cover_medium') or album.get('cover')
                
                if preview_url:
                    results.append({
                        'title': track_name,
                        'url': preview_url,
                        'thumbnail': artwork
                    })
    except:
        pass
    return results[:5]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🎧 Добро пожаловать в музыкальный бот (Deezer Edition)!\n\n"
        "🚀 Просто отправь название трека, и я сразу найду его!\n\n"
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
    
    for track_name in POPULAR_TRACKS:
        res = search_tracks(track_name)
        if res:
            entries.append(res[0])

    if not entries:
        await update.message.reply_text("❌ Не удалось загрузить топ треков.")
        return

    search_cache[user_id] = entries
    for i, entry in enumerate(entries, 1):
        response_text += f"🎵 **{i}. {entry['title']}**\n"
        row.append(InlineKeyboardButton(str(i), callback_data=f"select_{i-1}"))
    
    keyboard.append(row)
    first_entry = entries[0]
    if first_entry.get('thumbnail'):
        await update.message.reply_photo(photo=first_entry['thumbnail'], caption=response_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        await update.message.reply_text(response_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

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

    status_msg = await update.message.reply_text("⚡ Ищу трек в Deezer... 🔍")
    
    entries = search_tracks(query)
    if not entries:
        try:
            await status_msg.edit_text("❌ Трек не найден. Попробуйте написать по-другому.")
        except:
            await update.message.reply_text("❌ Трек не найден. Попробуйте написать по-другому.")
        return

    search_cache[user.id] = entries
    
    response_text = f"🎧 Запрос: *{query}*\n\n🎵 **Самые лучшие результаты:**\n\n"
    keyboard = []
    row = []
    for i, entry in enumerate(entries[:5], 1):
        response_text += f"🔹 **{i}. {entry['title']}**\n"
        row.append(InlineKeyboardButton(str(i), callback_data=f"select_{i-1}"))
    keyboard.append(row)

    try:
        await status_msg.delete()
    except:
        pass
    
    first_entry = entries[0]
    if first_entry.get('thumbnail'):
        await update.message.reply_photo(
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
            try:
                await query.message.reply_text("⚠️ Срок поиска истек. Отправьте запрос заново.")
            except:
                pass
            return

        selected = entries[index]
        title = selected.get('title', 'Музыка')
        thumbnail = selected.get('thumbnail')
        audio_url = selected.get('url')
        
        try:
            caption_text = f"🎵 *{title}*\n\n✨ Приятного прослушивания!\n👑 Администратор: {ADMIN_USER}"
            
            if thumbnail:
                await query.message.reply_photo(
                    photo=thumbnail,
                    caption=caption_text,
                    parse_mode="Markdown"
                )

            await query.message.reply_audio(
                audio=audio_url,
                title=title
            )
        except Exception as e:
            try:
                await query.message.reply_text("❌ Аудиофайлын табууга болбоду. Башка тректи көрүңүз.")
            except:
                pass

if __name__ == "__main__":
    Thread(target=run).start()
    bot = ApplicationBuilder().token(TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("top", top_command))
    bot.add_handler(CallbackQueryHandler(button_callback))
    bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    bot.run_polling()
