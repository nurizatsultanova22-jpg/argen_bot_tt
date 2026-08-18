import os
import glob
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

def search_soundcloud(query):
    # Тек гана SoundCloud'дон издейбиз (YouTube жок!)
    results = []
    try:
        ydl_opts = {
            'default_search': 'scsearch5',
            'quiet': True,
            'extract_flat': True,
            'noplaylist': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            res = ydl.extract_info(f"scsearch5:{query}", download=False)
            for entry in res.get('entries', []):
                title = entry.get('title')
                url = entry.get('url')
                if title and url:
                    results.append({'title': title, 'url': url})
    except:
        pass
    return results[:5]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🎧 SoundCloud Музыка ботко кош келиңиз!\n\n"
        "🚀 Ырдын атын жазсаңыз, SoundCloud'дон сүрөтү жана толук файлы менен таап берем!\n\n"
        f"👑 Администратор: {ADMIN_USER}"
    )
    await update.message.reply_text(welcome_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    if not query: return
    
    status_msg = await update.message.reply_text("🔎 SoundCloud'дан изделүүдө...")
    entries = search_soundcloud(query)
    
    if not entries:
        await status_msg.edit_text("❌ SoundCloud'дан ыр табылган жок.")
        return

    search_cache[update.effective_user.id] = entries
    
    text = f"🎧 Сурам: *{query}*\n\n🎵 **Жыйынтыктар (SoundCloud):**\n\n"
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
    track_url = entry['url']
    
    status_msg = await query.message.reply_text(f"⏳ SoundCloud'дон жүктөлүүдө: *{title}*...", parse_mode="Markdown")
    
    filename_pattern = "temp_audio.*"
    for f in glob.glob(filename_pattern): 
        try: os.remove(f)
        except: pass

    try:
        # Тек SoundCloud тректерин жүктөө опциясы
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'temp_audio.%(ext)s',
            'quiet': True,
            'noplaylist': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(track_url, download=True)
            thumb_url = info.get('thumbnail')
            
            downloaded_files = glob.glob(filename_pattern)
            if not downloaded_files:
                raise Exception("Файл табылган жок")
            
            file_path = downloaded_files[0]
            
            if thumb_url:
                await query.message.reply_photo(photo=thumb_url, caption=f"🎵 *{title}*", parse_mode="Markdown")
            
            with open(file_path, 'rb') as f:
                await query.message.reply_audio(audio=f, title=title, caption=f"👑 Admin: {ADMIN_USER}")
            
            for f in glob.glob(filename_pattern):
                try: os.remove(f)
                except: pass
                
            await status_msg.delete()
            
    except Exception as e:
        for f in glob.glob(filename_pattern):
            try: os.remove(f)
            except: pass
        await status_msg.edit_text("❌ Жүктөөдө ката кетти. Башка тректи тандаңыз.")

if __name__ == "__main__":
    Thread(target=run).start()
    bot = ApplicationBuilder().token(TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CallbackQueryHandler(button_callback))
    bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    bot.run_polling()
