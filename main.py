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

def search_deezer(query):
    results = []
    try:
        encoded_q = urllib.parse.quote(query)
        url = f"https://api.deezer.com/search?q={encoded_q}&limit=5"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            for item in data.get('data', []):
                title = f"{item['artist']['name']} - {item['title']}"
                # Deezer'ден 30 секунддук превью же толук тректи издөө үчүн шилтеме
                results.append({
                    'title': title,
                    'preview': item.get('preview'),
                    'thumbnail': item['artist'].get('picture_medium')
                })
    except:
        pass
    return results

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🎧 Deezer Музыка ботко кош келиңиз!\n\n"
        "🚀 Ырдын атын жазсаңыз, сүрөтү жана файлы менен заматта таап берем!\n\n"
        f"👑 Администратор: {ADMIN_USER}"
    )
    await update.message.reply_text(welcome_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    if not query: return
    
    status_msg = await update.message.reply_text("🔎 Deezer'ден изделүүдө...")
    entries = search_deezer(query)
    
    if not entries:
        await status_msg.edit_text("❌ Ыр табылган жок.")
        return

    search_cache[update.effective_user.id] = entries
    
    text = f"🎧 Сурам: *{query}*\n\n🎵 **Жыйынтыктар:**\n\n"
    keyboard = []
    for i, e in enumerate(entries):
        text += f"🔹 **{i+1}. {e['title']}**\n"
        keyboard.append([InlineKeyboardButton(f"🎵 {i+1}. {e['title'][:30]}...", callback_data=f"play_{i}")])
    
    await status_msg.delete()
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    index = int(query.data.split("_")[1])
    entries = search_cache.get(query.from_user.id)
    
    if not entries or index >= len(entries):
        await query.message.reply_text("⚠️ Сурам эскирди, кайра издеңиз.")
        return

    entry = entries[index]
    title = entry['title']
    thumb_url = entry.get('thumbnail')
    
    status_msg = await query.message.reply_text(f"⏳ Жүктөлүүдө: *{title}*...", parse_mode="Markdown")
    
    try:
        # Deezer превью аудиосун түздөн-түз жүктөө
        preview_url = entry['preview']
        if not preview_url:
            raise Exception("Файл жок")
            
        file_path = "temp_audio.mp3"
        urllib.request.urlretrieve(preview_url, file_path)
        
        if thumb_url:
            await query.message.reply_photo(photo=thumb_url, caption=f"🎵 *{title}*", parse_mode="Markdown")
        
        with open(file_path, 'rb') as f:
            await query.message.reply_audio(audio=f, title=title, caption=f"👑 Admin: {ADMIN_USER}")
        
        if os.path.exists(file_path):
            os.remove(file_path)
            
        await status_msg.delete()
            
    except Exception as e:
        if os.path.exists("temp_audio.mp3"):
            os.remove("temp_audio.mp3")
        await status_msg.edit_text("❌ Жүктөөдө ката кетти. Башка тректи тандаңыз.")

if __name__ == "__main__":
    Thread(target=run).start()
    bot = ApplicationBuilder().token(TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CallbackQueryHandler(button_callback))
    bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    bot.run_polling()
