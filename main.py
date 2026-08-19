import os
import glob
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
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
    'default_search': 'scsearch1',
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

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🔥 Популярдуу тректер"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    text = (
        "👋 Салам! Мен музыка ботумун.\n\n"
        "🎵 Каалаган ырдын атын түздөн-түз жазып издей аласыз.\n"
        "🔥 Же төмөнкү кнопка аркылуу популярдуу тректерди көрүңүз 👇\n\n"
        f"ℹ️ Бот Арген тарабынан түзүлгөн. Админ: {ADMIN_USER}"
    )
    await update.message.reply_text(text, reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    query = update.message.text
    if not query: return
    
    if query == "🔥 Популярдуу тректер":
        keyboard = [
            [InlineKeyboardButton("🎵 Bakr - Мадина", callback_data="pop_1")],
            [InlineKeyboardButton("🎵 ALHAM - Хикаям", callback_data="pop_2")],
            [InlineKeyboardButton("🎵 Хип-хоп хиттер", callback_data="pop_3")]
        ]
        await update.message.reply_text("🔥 Учурда трендде болгон тректер:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    search_query = query.strip()
    status_msg = await update.message.reply_text("🔎 SoundCloud'дан изделүүдө...")
    
    try:
        with yt_dlp.YoutubeDL(YDL_OPTS_SEARCH) as ydl:
            res = yt_dlp.YoutubeDL(YDL_OPTS_SEARCH).extract_info(f"scsearch1:{search_query}", download=False)
            entries = res.get('entries', [])
            if not entries:
                raise Exception("Табылган жок")
            
            entry = entries[0]
            track_info = {
                'title': entry.get('title', search_query),
                'url': entry.get('url'),
                'thumbnail': entry.get('thumbnail')
            }
            
            search_cache[user_id] = track_info
            keyboard = [[InlineKeyboardButton("🎵 Жүктөп алуу", callback_data="download_track")]]
            text = f"🎧 Табылды:\n\n🔹 {track_info['title']}"
            
            await status_msg.delete()
            if track_info.get('thumbnail'):
                # Ырдын сүрөтүн чоң чакан сүрөт (фону менен) катары жиберет
                await update.message.reply_photo(photo=track_info['thumbnail'], caption=text, reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
            return
    except:
        await status_msg.edit_text("❌ Көрсөтүлгөн ыр табылган жок, башка атын жазып көрүңүз.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data.startswith("pop_"):
        songs = {
            "pop_1": "Bakr Madina",
            "pop_2": "ALHAM Hikayam",
            "pop_3": "Top Rap Remix"
        }
        search_query = songs.get(data, "Hit music")
        status_msg = await query.message.reply_text("🔎 Популярдуу трек изделүүдө...")
        
        try:
            with yt_dlp.YoutubeDL(YDL_OPTS_SEARCH) as ydl:
                res = ydl.extract_info(f"scsearch1:{search_query}", download=False)
                entries = res.get('entries', [])
                if not entries: raise Exception()
                
                entry = entries[0]
                track_info = {
                    'title': entry.get('title', search_query),
                    'url': entry.get('url'),
                    'thumbnail': entry.get('thumbnail')
                }
                search_cache[query.from_user.id] = track_info
                keyboard = [[InlineKeyboardButton("🎵 Жүктөп алуу", callback_data="download_track")]]
                text = f"🎧 Табылды:\n\n🔹 {track_info['title']}"
                
                await status_msg.delete()
                if track_info.get('thumbnail'):
                    await query.message.reply_photo(photo=track_info['thumbnail'], caption=text, reply_markup=InlineKeyboardMarkup(keyboard))
                else:
                    await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
                return
        except:
            await status_msg.edit_text("❌ Ката кетти.")
            return

    track = search_cache.get(query.from_user.id)
    if not track:
        await query.message.reply_text("⚠️ Ката чыкты, кайра издеңиз.")
        return

    status_msg = await query.message.reply_text(f"⏳ Жүктөлүүдө: {track['title']}...")
    
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
    bot.add_handler(CommandHandler("start", start_command))
    bot.add_handler(CallbackQueryHandler(button_callback))
    bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    bot.run_polling()
