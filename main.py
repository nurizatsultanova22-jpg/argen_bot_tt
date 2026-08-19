import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

TOKEN = "8558649634:AAHEqz0qKwSg46pcqme0D84pLsdAmVIe8p8"

app_web = Flask(__name__)
@app_web.route('/')
def home():
    return "Bot is active!"

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

    # Telegram аркылуу даяр аудио файлдарды табуу көрсөтмөсү
    await update.message.reply_text(
        f"🎵 Арген, бул тректи түздөн-түз табуу үчүн боттун атын басып же @music боттор сыяктуу издесең, толук файл заматта келет.\n\n"
        f"👉 Текшерүү үчүн жеңил баскычтарды коштук, изделген трек: **{query}**",
        parse_mode=ParseMode.MARKDOWN
    )

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
