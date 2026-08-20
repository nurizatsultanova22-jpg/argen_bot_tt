import os
import threading
import requests
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

TOKEN = "8845409356:AAFjm-nh9q_aWPyfUVHx8v0k-sHYeFtoJgA"

app_web = Flask(__name__)
@app_web.route('/')
def home():
    return "Bot is active!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host="0.0.0.0", port=port)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower().strip()
    if not (text.startswith("найди") or text.startswith("трек")): return

    query = text.replace("найди", "").replace("трек", "").strip()
    if not query: return

    status = await update.message.reply_text("🔍 *Ищу трек...* 🎧", parse_mode=ParseMode.MARKDOWN)

    try:
        # Deezer аркылуу издөө
        search_url = f"https://api.deezer.com/search?q={query}"
        response = requests.get(search_url).json()
        
        if 'data' in response and len(response['data']) > 0:
            track = response['data'][0]
            title = track['title']
            artist = track['artist']['name']
            cover = track['album']['cover_big']
            audio_url = track['preview'] # Бул превью, бирок иштегени так

            await update.message.reply_photo(photo=cover, caption=f"🎵 {artist} — {title}")
            await update.message.reply_audio(audio=audio_url, title=title, performer=artist)
            await status.delete()
        else:
            await status.edit_text("❌ *Трек не найден.*")
    except Exception:
        await status.edit_text("❌ *Ошибка.*")

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
