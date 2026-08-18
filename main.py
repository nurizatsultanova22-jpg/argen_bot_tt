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
def home(): return "Бот иштеп жатат!"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))

search_cache = {}

def search_soundcloud(query):
    # SoundCloud'дан издөө - YouTube'ду такыр колдонбойбуз (бөгөт болбойт)
    ydl_opts = {
        'default_search': 'scsearch5',
        'quiet': True,
        'extract_flat': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        res = ydl.extract_info(f"scsearch5:{query}", download=False)
        return res.get('entries', [])

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    if not query: return
    
    status_msg = await update.message.reply_text("🔎 SoundCloud'дан изделүүдө...")
    entries = search_soundcloud(query)
    
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
    entry = search_cache[query.from_user.id][index]
    title = entry['title']
    
    status_msg = await query.message.reply_text(f"⏳ Жүктөлүүдө: *{title}*...", parse_mode="Markdown")
    
    try:
        # Аудио жана обложканы алуу
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'temp_audio.%(ext)s',
            'quiet': True,
            'noplaylist': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(entry['url'], download=True)
            # yt-dlp автоматтык түрдө форматты тандайт (mp3/m4a)
            file_path = f"temp_audio.{info['ext']}"
            thumb_url = info.get('thumbnail')
            
            # Обложка менен жөнөтүү
            if thumb_url:
                await query.message.reply_photo(photo=thumb_url, caption=f"🎵 *{title}*", parse_mode="Markdown")
            
            with open(file_path, 'rb') as f:
                await query.message.reply_audio(audio=f, title=title, caption=f"👑 Admin: {ADMIN_USER}")
            
            os.remove(file_path)
            await status_msg.delete()
            
    except Exception as e:
        await status_msg.edit_text("❌ Ката кетти. Башка тректи тандаңыз.")

if __name__ == "__main__":
    Thread(target=run).start()
    bot = ApplicationBuilder().token(TOKEN).build()
    bot.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("Салам! Ырдын атын жаз.")))
    bot.add_handler(CallbackQueryHandler(button_callback))
    bot.add_handler(MessageHandler(filters.TEXT, handle_message))
    bot.run_polling()
