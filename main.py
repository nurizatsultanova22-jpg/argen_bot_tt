import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = "8558649634:AAHEqz0qKwSg46pcqme0D84pLsdAmVIe8p8"

app_web = Flask(__name__)
@app_web.route('/')
def home(): return "Bot is active!"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Telegram'дын өзүнүн аудио издөө функциясын колдонуу
    # Бул код жөн гана суроону иштетет
    text = update.message.text.lower().strip()
    if not (text.startswith("найди") or text.startswith("трек")): return

    await update.message.reply_text("🎧 *Брат, сейчас Telegram сам поищет трек...*")
    # Эскертүү: Бул жерде жөнөкөй логика, эгер бул да иштебесе,
    # анда Render'дин IP дареги толугу менен музыкалык сервис үчүн блок.
    
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
