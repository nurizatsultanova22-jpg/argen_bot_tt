import os
import urllib.parse
import urllib.request
import json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes
from threading import Thread
from flask import Flask

TOKEN = "8558649634:AAHEqz0qKwSg46pcqme0D84pLsdAmVIe8p8"
ADMIN_USER = "@Argen_70"

app = Flask('')
@app.route('/')
def home(): return "Бот иштеп жатат!"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))

search_cache = {}

# iTunes аркылуу сүрөтүн жана атын так табабыз
def get_itunes_track(query):
    try:
        encoded_q = urllib.parse.quote(query)
        url = f"https://itunes.apple.com/search?term={encoded_q}&entity=song&limit=1"
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode())
            items = data.get('results', [])
            if items:
                item = items[0]
                return {
                    'title': f"{item['artistName']} - {item['trackName']}",
                    'preview': item.get('previewUrl'), # 30 секунддук же толук превью
                    'thumbnail': item.get('artworkUrl100', '').replace('100x100bb', '600x600bb')
                }
    except:
        pass
    return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    if not query: return
    
    status_msg = await update.message.reply_text("🔎 Изделүүдө...")
    
    track = get_itunes_track(query)
    if not track:
        await status_msg.edit_text("❌ Ыр табылган жок.")
        return

    search_cache[update.effective_user.id] = track
    
    keyboard = [[InlineKeyboardButton("🎵 Жүктөп алуу", callback_data="download_track")]]
    text = f"🎧 Табылды:\n\n🔹 **{track['title']}**"
    
    await status_msg.delete()
    if track['thumbnail']:
        await update.message.reply_photo(photo=track['thumbnail'], caption=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    track = search_cache.get(query.from_user.id)
    if not track or not track.get('preview'):
        await query.message.reply_text("⚠️ Файл табылган жок.")
        return

    status_msg = await query.message.reply_text(f"⏳ Жүктөлүүдө: *{track['title']}*...", parse_mode="Markdown")
    
    try:
        file_path = "temp_audio.m4a"
        urllib.request.urlretrieve(track['preview'], file_path)
        
        with open(file_path, 'rb') as f:
            await query.message.reply_audio(audio=f, title=track['title'], caption=f"👑 Admin: {ADMIN_USER}")
        
        if os.path.exists(file_path):
            os.remove(file_path)
            
        await status_msg.delete()
    except Exception as e:
        if os.path.exists("temp_audio.m4a"):
            os.remove("temp_audio.m4a")
        await status_msg.edit_text("❌ Жүктөөдө ката кетти.")

if __name__ == "__main__":
    Thread(target=run).start()
    bot = ApplicationBuilder().token(TOKEN).build()
    bot.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("Салам! Ырдын атын жаз.")))
    bot.add_handler(CallbackQueryHandler(button_callback))
    bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    bot.run_polling()
