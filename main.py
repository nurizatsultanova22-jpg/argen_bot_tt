import os
import threading
from flask import Flask
from spotdl import Spotdl
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = "8558649634:AAHEqz0qKwSg46pcqme0D84pLsdAmVIe8p8"

# Spotify Downloader инициализациясы
spotdl = Spotdl(client_id='4a86488d011e4001944cc996e38eb20a', client_secret='470a8d6728c34f9a888c3a77a9173007')

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

    status = await update.message.reply_text("🔍 *Ищу на Spotify...* 🎧")

    try:
        # Издөө жана жүктөө
        results = spotdl.search([query])
        song = spotdl.download(results[0])
        
        await update.message.reply_audio(audio=open(song.path, 'rb'))
        
        await status.delete()
        if os.path.exists(song.path): os.remove(song.path)
    except Exception:
        await status.edit_text("❌ *Трек не найден.*")

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
