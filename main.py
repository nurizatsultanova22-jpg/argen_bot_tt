import os
import threading
from flask import Flask
from google import genai
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

TELEGRAM_TOKEN = "8943857517:AAHKx8raz2WrxYeHI2hjE1f5TpnygJq2vZE"
GEMINI_API_KEY = "AQ.Ab8RN6K1BMjpXD5H2tiulT-G04N5OQm-j..." # Өзүңдүн толук AQ ачкычыңды жаз

# Жаңы google-genai SDK аркылуу туташуу
client = genai.Client(api_key=GEMINI_API_KEY)
MODEL_ID = "gemini-1.5-flash"

app_web = Flask(__name__)
@app_web.route('/')
def home():
    return "Gemini Bot is active!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host="0.0.0.0", port=port)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[KeyboardButton("Подключить Gemini")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Привет! Нажми кнопку ниже, чтобы начать работу с Gemini.", reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "Подключить Gemini":
        await update.message.reply_text("✅ Gemini подключен! Задавай любой вопрос.")
        return

    status = await update.message.reply_text("⏳ *Думаю...*", parse_mode="Markdown")
    try:
        # Жаңы SDK боюнча суроо жөнөтүү
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=text,
        )
        await update.message.reply_text(response.text)
        await status.delete()
    except Exception as e:
        await status.edit_text(f"❌ Ошибка: {str(e)[:50]}")

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
