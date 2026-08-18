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

YDL_OPTS_SEARCH = {
    'default_search': 'scsearch1', # SoundCloud'дон 1 гана так вариант
    'quiet': True,
    'extract_flat': True,
    'http_headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
}

YDL_OPTS_DOWNLOAD = {
    'format': 'bestaudio/best',
    'outtmpl': 'temp_audio.%(ext)s',
    'quiet': True,
    'noplaylist': True,
    'http_headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    if not query: return
    
    status_msg = await update.message.reply_text("🔎 SoundCloud'дан изделүүдө...")
    
    try:
        with yt_dlp.YoutubeDL(YDL_OPTS_SEARCH) as ydl:
            res = ydl.extract_info(f"scsearch1:{query}", download=False)
            entries = res.get('entries', [])
            if not entries:
                raise Exception("Табылган жок")
            
            entry = entries[0]
            track_info = {
                'title': entry.get('title', query),
                'url': entry.get('url'),
                'thumbnail': entry.get('thumbnail')
            }
    except:
        await status_msg.edit_text("❌ SoundCloud'дан ыр табылган жок.")
        return

    search_cache[update.effective_user.id] = track_info
    
    keyboard = [[InlineKeyboardButton("🎵 Жүктөп алуу", callback_data="download_track")]]
    text = f"🎧 Табылды (SoundCloud):\n\n🔹 **{track_info['title']}**"
    
    await status_msg.delete()
    if track_info.get('thumbnail'):
        await update.message.reply_photo(photo=track_info['thumbnail'], caption=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    track = search_cache.get(query.from_user.id)
    if not track:
        await query.message.reply_text("⚠️ Ката чыкты, кайра издеңиз.")
        return

    status_msg = await query.message.reply_text(f"⏳ Жүктөлүүдө: *{track['title']}*...", parse_mode="Markdown")
    
    for f in glob.glob("temp_audio.*"): 
        try: os.remove(f)
        except: pass

    try:
        with yt_dlp.YoutubeDL(YDL_OPTS_DOWNLOAD) as ydl:
            ydl.extract_info(track['url'], download=True)
            downloaded = glob.glob("temp_audio.*")
            if not downloaded:
                raise Exception("Файл табылган жок")
            
            file_path = downloaded[0]
            
            with open(file_path, 'rb') as f:
                await query.message.reply_audio(audio=f, title=track['title'], caption=f"👑 Admin: {ADMIN_USER}")
            
            os.remove(file_path)
            await status_msg.delete()
    except Exception as e:
        for f in glob.glob("temp_audio.*"): 
            try: os.remove(f)
            except: pass
        await status_msg.edit_text("❌ Жүктөөдө ката кетти.")

if __name__ == "__main__":
    Thread(target=run).start()
    bot = ApplicationBuilder().token(TOKEN).build()
    bot.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("Салам! SoundCloud музыка ботко кош келиңиз. Ырдын атын жаз.")))
    bot.add_handler(CallbackQueryHandler(button_callback))
    bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    bot.run_polling()
