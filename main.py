import os
import glob
import urllib.parse
import urllib.request
import json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes
from threading import Thread
from flask import Flask
import yt_dlp

TOKEN = "8558649634:AAHEqz0qKwSg46pcqme0D84pLsdAmVIe8p8"
ADMIN_USER = "@Argen_70"

app = Flask('')
@app.route('/')
def home(): return "Бот иштеп жатат!"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))

search_cache = {}

# 1. iTunes аркылуу 5 так вариантты жана сүрөтүн алабыз
def get_itunes_results(query):
    try:
        encoded_q = urllib.parse.quote(query)
        url = f"https://itunes.apple.com/search?term={encoded_q}&entity=song&limit=5"
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode())
            results = []
            for item in data.get('results', []):
                results.append({
                    'title': f"{item['artistName']} - {item['trackName']}",
                    'thumbnail': item.get('artworkUrl100', '').replace('100x100bb', '600x600bb')
                })
            return results
    except:
        return []

# 2. SoundCloud'дан толук ырды жүктөп алабыз
YDL_OPTS = {
    'format': 'bestaudio/best',
    'outtmpl': 'temp_audio.%(ext)s',
    'quiet': True,
    'noplaylist': True,
    'default_search': 'scsearch1',
    'http_headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}
}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    status_msg = await update.message.reply_text("🔎 Изделүүдө...")
    
    entries = get_itunes_results(query)
    if not entries:
        await status_msg.edit_text("❌ Ыр табылган жок.")
        return

    search_cache[update.effective_user.id] = entries
    
    keyboard = [[InlineKeyboardButton(f"🎵 {i+1}", callback_data=f"play_{i}")] for i in range(len(entries))]
    
    text = f"🎧 Сурам: *{query}*\n\n" + "\n".join([f"{i+1}. {e['title']}" for i, e in enumerate(entries)])
    
    await status_msg.delete()
    # Сүрөт үстүндө турат
    await update.message.reply_photo(photo=entries[0]['thumbnail'], caption=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    index = int(query.data.split("_")[1])
    entry = search_cache.get(query.from_user.id)[index]
    
    status_msg = await query.message.reply_text(f"⏳ Жүктөлүүдө: *{entry['title']}*...")
    
    # Эски файлдарды тазалоо
    for f in glob.glob("temp_audio.*"): os.remove(f)

    try:
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            ydl.download([f"scsearch1:{entry['title']}"])
            file_path = glob.glob("temp_audio.*")[0]
            
            await query.message.reply_audio(audio=open(file_path, 'rb'), title=entry['title'], caption=f"👑 Admin: {ADMIN_USER}")
            os.remove(file_path)
            await status_msg.delete()
    except:
        await status_msg.edit_text("❌ Ката кетти.")

if __name__ == "__main__":
    Thread(target=run).start()
    bot = ApplicationBuilder().token(TOKEN).build()
    bot.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("Ырдын атын жаз.")))
    bot.add_handler(CallbackQueryHandler(button_callback))
    bot.add_handler(MessageHandler(filters.TEXT, handle_message))
    bot.run_polling()
