import os
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes
from threading import Thread
from flask import Flask

TOKEN = "8558649634:AAHEqz0qKwSg46pcqme0D84pLsdAmVIe8p8"

app = Flask('')
@app.route('/')
def home(): return "Бот работает! 🚀"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = ReplyKeyboardMarkup([["🔥 Популярное", "🎧 Новинки"]], resize_keyboard=True)
    await update.message.reply_text("Привет! Напиши название песни, и я скачаю полную версию через SpotDL! 🎵", reply_markup=reply_markup)

async def search_and_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    if not query: return
    
    if query in ["🔥 Популярное", "🎧 Новинки"]:
        query = "Top hits"
    
    status = await update.message.reply_text("🔍 Ищу трек...")
    
    try:
        # SpotDL аркылуу ырды издеп, маалыматын алуу (терминал аркылуу же spotdl китепканасы менен)
        import subprocess
        # SpotDL издөө жасап, шилтемесин табуу командасы
        cmd = f"spotdl --print-urls \"{query}\""
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        urls = result.stdout.strip().split('\n')
        
        if not urls or not urls[0]:
            await status.edit_text("❌ Ничего не найдено.")
            return

        track_url = urls[0]
        context.user_data['track_url'] = track_url
        
        await status.edit_text("⏳ Скачиваю полную версию песни...")
        
        # SpotDL аркылуу ырды серверге жүктөө
        download_cmd = f"spotdl {track_url} --output ."
        subprocess.run(download_cmd, shell=True)
        
        # Жүктөлгөн MP3 файлын табуу
        mp3_files = [f for f in os.listdir('.') if f.endswith('.mp3')]
        
        if mp3_files:
            latest_file = max(mp3_files, key=os.path.getctime)
            with open(latest_file, 'rb') as audio:
                await update.message.reply_audio(audio=audio, caption="Готово! 🎶")
            os.remove(latest_file)
            await status.delete()
        else:
            await status.edit_text("❌ Не удалось скачать файл.")
            
    except Exception as e:
        await status.edit_text("❌ Произошла ошибка при загрузке.")

if __name__ == "__main__":
    Thread(target=run).start()
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), search_and_send))
    app_bot.run_polling()
