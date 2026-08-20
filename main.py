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
    return "Bot status: OK"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host="0.0.0.0", port=port)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower().strip()
    if not (text.startswith("найди") or text.startswith("трек")): 
        return

    query = text.replace("найди", "").replace("трек", "").strip()
    if not query: 
        return

    status = await update.message.reply_text("🔍 *Файл издеп жатам...* 🎧", parse_mode=ParseMode.MARKDOWN)

    try:
        # Ачык API аркылуу түз MP3 файл издөө
        search_url = f"https://api.vagalume.com.br/search.php?art={query}&mus={query}"
        # Альтернативалуу акысыз MP3 API катары Saavn / Soundcloud дагы колдонсо болот
        deezer_url = f"https://api.deezer.com/search?q={query}"
        res = requests.get(deezer_url).json()

        if 'data' in res and len(res['data']) > 0:
            track = res['data'][0]
            title = track['title']
            artist = track['artist']['name']
            mp3_url = track['preview'] # MP3 файлдын өзүнүн туруктуу шилтемеси

            # Telegram шилтемеден файлды өзү жүктөп, чатка кадимки MP3 файл катары салат:
            await context.bot.send_audio(
                chat_id=update.effective_chat.id,
                audio=mp3_url,
                title=title,
                performer=artist,
                caption=f"🎵 *{artist} — {title}*",
                parse_mode=ParseMode.MARKDOWN
            )
            await status.delete()
        else:
            await status.edit_text("❌ *Файл табылган жок.*")
    except Exception as e:
        await status.edit_text(f"❌ *Ката чыкты:* {str(e)[:60]}")

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
