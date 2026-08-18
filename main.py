import os
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
def home(): return "Бот работает идеально!"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))

search_cache = {}

def search_tracks(query):
    results = []
    try:
        encoded_q = urllib.parse.quote(query)
        url = f"https://itunes.apple.com/search?term={encoded_q}&entity=song&limit=5"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            for item in data.get('results', []):
                track_name = f"{item.get('artistName', '')} - {item.get('trackName', '')}"
                artwork = item.get('artworkUrl100', '').replace('100x100bb', '600x600bb')
                results.append({
                    'title': track_name,
                    'thumbnail': artwork
                })
    except:
        pass
    return results[:5]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🎧 Музыка ботко кош келиңиз!\n\n"
        "🚀 Ырдын атын жазыңыз, мен атын, сүрөтүн жана өзүн таап берем!\n\n"
        f"👑 Администратор: {ADMIN_USER}"
    )
    await update.message.reply_text(welcome_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    query = (update.message.text or "").strip()
    if not query: return

    status_msg = await update.message.reply_text("⚡ Ыр изделүүдө... 🔍")
    
    entries = search_tracks(query)
    if not entries:
        await status_msg.edit_text("❌ Ыр табылган жок. Атын тактап кайра жазыңыз.")
        return

    search_cache[user.id] = entries
    
    response_text = f"🎧 Сурам: *{query}*\n\n🎵 **Жыйынтыктар:**\n\n"
    keyboard = []
    
    for i, entry in enumerate(entries):
        response_text += f"🔹 **{i+1}. {entry['title']}**\n"
        keyboard.append([InlineKeyboardButton(f"🎵 {i+1}", callback_data=f"select_{i}")])

    await status_msg.delete()
    
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
            await query.message.reply_text("⚠️ Сурам эскирди, ырды кайра издеңиз.")
            return

        selected = entries[index]
        title = selected['title']
        thumbnail = selected.get('thumbnail')
        
        status_msg = await query.message.reply_text(f"⏳ Жүктөлүүдө: *{title}*...", parse_mode="Markdown")

        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'default_search': f"ytsearch:{title}",
                'outtmpl': 'temp_audio.mp3',
                'quiet': True,
                'noplaylist': True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([f"ytsearch:{title}"])
            
            if os.path.exists('temp_audio.mp3'):
                if thumbnail:
                    await query.message.reply_photo(photo=thumbnail, caption=f"🎵 *{title}*", parse_mode="Markdown")
                
                with open('temp_audio.mp3', 'rb') as f:
                    await query.message.reply_audio(
                        audio=f,
                        title=title,
                        caption=f"✨ Приятного прослушивания!\n👑 Администратор: {ADMIN_USER}"
                    )
                os.remove('temp_audio.mp3')
            else:
                raise Exception("File not found")

            await status_msg.delete()
        except Exception as e:
            if os.path.exists('temp_audio.mp3'):
                os.remove('temp_audio.mp3')
            await status_msg.edit_text("❌ Файлды жүктөөдө ката кетти. Башка тректи тандаңыз.")

if __name__ == "__main__":
    Thread(target=run).start()
    bot = ApplicationBuilder().token(TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CallbackQueryHandler(button_callback))
    bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    bot.run_polling()
