import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes
from threading import Thread
from flask import Flask
import yt_dlp

TOKEN = "8558649634:AAHEqz0qKwSg46pcqme0D84pLsdAmVIe8p8"
ADMIN_USER = "@Argen_70"

app = Flask('')
@app.route('/')
def home(): return "Бот ийгиликтүү иштеп жатат!"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))

search_cache = {}

def search_tracks(query):
    results = []
    try:
        ydl_opts = {
            'default_search': 'scsearch5',
            'quiet': True,
            'extract_flat': True,
            'noplaylist': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            res = yt_dlp.YoutubeDL(ydl_opts).extract_info(f"scsearch5:{query}", download=False)
            for entry in res.get('entries', []):
                title = entry.get('title')
                url = entry.get('url')
                if title and url:
                    results.append({
                        'title': title,
                        'url': url
                    })
    except:
        pass
    return results[:5]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🎧 SoundCloud Музыка ботко кош келиңиз!\n\n"
        "🚀 Жөн гана ырдын атын же аткаруучуну жазып жибериңиз.\n\n"
        f"👑 Администратор: {ADMIN_USER}"
    )
    await update.message.reply_text(welcome_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    query = (update.message.text or "").strip()
    if not query: return

    status_msg = await update.message.reply_text("⚡ SoundCloud'дан изделүүдө... 🔍")
    
    entries = search_tracks(query)
    if not entries:
        await status_msg.edit_text("❌ Ыр табылган жок. Атын тактап кайра жазыңыз.")
        return

    search_cache[user.id] = entries
    
    response_text = f"🎧 Сурам: *{query}*\n\n🎵 **Жыйынтыктар:**\n\n"
    keyboard = []
    
    for i, entry in enumerate(entries):
        response_text += f"🔹 **{i+1}. {entry['title']}**\n"
        keyboard.append([InlineKeyboardButton(f"🎵 {i+1}. {entry['title'][:30]}...", callback_data=f"select_{i}")])

    await status_msg.delete()
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
        track_url = selected['url']
        
        status_msg = await query.message.reply_text(f"⏳ Даярдалууда: *{title}*...", parse_mode="Markdown")

        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': 'temp_audio.mp3',
                'quiet': True,
                'noplaylist': True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(track_url, download=True)
                audio_file_path = 'temp_audio.mp3'
                if os.path.exists(audio_file_path):
                    with open(audio_file_path, 'rb') as f:
                        await query.message.reply_audio(
                            audio=f,
                            title=title,
                            caption=f"✨ Приятного прослушивания!\n👑 Администратор: {ADMIN_USER}"
                        )
                    os.remove(audio_file_path)
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
