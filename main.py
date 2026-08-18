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

# iTunes аркылуу ырдын сүрөтүн жана атын так табабыз (обложка үчүн)
def get_itunes_cover(query):
    try:
        encoded_q = urllib.parse.quote(query)
        url = f"https://itunes.apple.com/search?term={encoded_q}&entity=song&limit=1"
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode())
            items = data.get('results', [])
            if items:
                return items[0].get('artworkUrl100', '').replace('100x100bb', '600x600bb')
    except:
        pass
    return None

# Free Public MP3 API аркылуу VK / Ineural базасынан толук ырды табуу
def search_vk_full_track(query):
    try:
        encoded_q = urllib.parse.quote(query)
        # Публичный музыкалык API (VK/MP3 базасы)
        api_url = f"https://itunes.apple.com/search?term={encoded_q}&entity=song&limit=1"
        # Бул жерде Альтернативдик толук аудио берүүчү ачык API колдонобуз
        pub_api = f"https://freesound.org/apiv2/search/text/?query={encoded_q}&token=guest&page_size=1"
        
        # Келгиле, эң стабилдүү Free MP3 search engine колдонолу:
        search_url = f"https://pipedapi.kavin.rocks/search?q={urllib.parse.quote(query + ' audio')}&filter=music"
        req = urllib.request.Request(search_url, headers={'User-Agent': 'Mozilla/5.0'})
        
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode())
            items = data.get('items', [])
            for item in items:
                if item.get('type') == 'stream' or 'duration' in item:
                    # Толук шилтемени алабыз
                    vid_id = item.get('url', '').split('=')[-1]
                    audio_link = f"https://pipedapi.kavin.rocks/streams/{vid_id}"
                    title = item.get('title', query)
                    thumbnail = get_itunes_cover(query) or item.get('thumbnail')
                    return {
                        'title': title,
                        'audio_url': audio_link,
                        'thumbnail': thumbnail
                    }
    except:
        pass
    
    # Эгер жогоркусу таппаса, түздөн-түз ачык MP3 поисковикке кайрылабыз
    try:
        fallback_url = f"https://archive.org/advancedsearch.php?q={urllib.parse.quote(query)}&fl[]=title&fl[]=identifier&rows=1&output=json"
        with urllib.request.urlopen(fallback_url, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            docs = data.get('response', {}).get('docs', [])
            if docs:
                identifier = docs[0].get('identifier')
                title = docs[0].get('title', query)
                audio_link = f"https://archive.org/download/{identifier}/{identifier}_vbr.mp3"
                thumbnail = get_itunes_cover(query)
                return {
                    'title': title,
                    'audio_url': audio_link,
                    'thumbnail': thumbnail
                }
    except:
        pass
        
    return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    if not query: return
    
    status_msg = await update.message.reply_text("🔎 VK музыка базасынан изделүүдө...")
    
    track = search_vk_full_track(query)
    if not track or not track.get('audio_url'):
        await status_msg.edit_text("❌ Ыр табылган жок. Башкача жазып көрүңүз.")
        return

    search_cache[update.effective_user.id] = track
    
    keyboard = [[InlineKeyboardButton("🎵 Жүктөп алуу", callback_data="download_track")]]
    text = f"🎧 Табылды:\n\n🔹 **{track['title']}**"
    
    await status_msg.delete()
    if track.get('thumbnail'):
        await update.message.reply_photo(photo=track['thumbnail'], caption=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    track = search_cache.get(query.from_user.id)
    if not track or not track.get('audio_url'):
        await query.message.reply_text("⚠️ Файл табылган жок.")
        return

    status_msg = await query.message.reply_text(f"⏳ Жүктөлүүдө: *{track['title']}*...", parse_mode="Markdown")
    
    try:
        file_path = "temp_audio.mp3"
        urllib.request.urlretrieve(track['audio_url'], file_path)
        
        with open(file_path, 'rb') as f:
            await query.message.reply_audio(audio=f, title=track['title'], caption=f"👑 Admin: {ADMIN_USER}")
        
        if os.path.exists(file_path):
            os.remove(file_path)
            
        await status_msg.delete()
    except Exception as e:
        if os.path.exists("temp_audio.mp3"):
            os.remove("temp_audio.mp3")
        await status_msg.edit_text("❌ Жүктөөдө ката кетти.")

if __name__ == "__main__":
    Thread(target=run).start()
    bot = ApplicationBuilder().token(TOKEN).build()
    bot.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("Салам! Ырдын атын жаз.")))
    bot.add_handler(CallbackQueryHandler(button_callback))
    bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    bot.run_polling()
