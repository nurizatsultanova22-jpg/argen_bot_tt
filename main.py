import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = "8558649634:AAHEqz0qKwSg46pcqme0D84pLsdAmVIe8p8"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    status = await update.message.reply_text("⏳ Интернеттен изделүүдө...")

    try:
        # Интернеттеги музыкалык ачык база аркылуу издөө
        search_url = f"https://itunes.apple.com/search?term={query}&entity=song&limit=1"
        res = requests.get(search_url).json()
        results = res.get('results', [])

        if not results:
            await status.edit_text("❌ Интернеттен бул ыр табылган жок.")
            return

        track = results[0]
        title = track.get('trackName', 'Музыка')
        artist = track.get('artistName', 'Белгисиз')
        audio_url = track.get('previewUrl') # 30 секунддук же толук превью
        artwork = track.get('artworkUrl100', '').replace('100x100bb.jpg', '600x600bb.jpg')

        if not audio_url:
            await status.edit_text("❌ Бул ырдын аудио шилтемеси жеткиликтүү эмес.")
            return

        # Аудио файлды жүктөө
        audio_data = requests.get(audio_url).content
        audio_file = "track.mp3"
        with open(audio_file, "wb") as f:
            f.write(audio_data)

        caption = f"🎵 **{artist} — {title}**\n👤 @Argen"

        if artwork:
            await update.message.reply_photo(photo=artwork, caption=caption, parse_mode="Markdown")

        await update.message.reply_audio(audio=open(audio_file, 'rb'), title=title, performer=artist)
        
        await status.delete()
        if os.path.exists(audio_file):
            os.remove(audio_file)

    except Exception:
        await status.edit_text("⚠️ Ката кетти, башка аталыш менен жазып көрүңүз.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
