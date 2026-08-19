import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = "8558649634:AAHEqz0qKwSg46pcqme0D84pLsdAmVIe8p8"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    status = await update.message.reply_text("🔍 Музыка изделүүдө...")

    try:
        # JioSaavn API ачык жана толук MP3 тректерди берет
        api_url = f"https://saavn.dev/api/search/songs?query={query}"
        response = requests.get(api_url).json()
        
        data = response.get('data', {}).get('results', [])
        if not data:
            await status.edit_text("❌ Кечиресиз, ыр табылган жок.")
            return

        track = data[0]
        title = track.get('name', 'Музыка')
        artist = track.get('artists', {}).get('primary', [{}])[0].get('name', 'Белгисиз')
        
        # 320kbps жогорку сапаттагы аудио шилтемеси
        download_url = track.get('downloadUrl', [{}])[-1].get('url')
        image_url = track.get('image', [{}])[2].get('link')

        if not download_url:
            await status.edit_text("❌ Аудио файлдын шилтемеси табылган жок.")
            return

        # Аудио файлды жүктөп алуу
        audio_data = requests.get(download_url).content
        audio_file = "song.mp3"
        with open(audio_file, 'wb') as f:
            f.write(audio_data)

        # Сүрөт менен жөнөтүү
        caption = f"🎵 **{artist} — {title}**\n👤 @Argen"
        
        if image_url:
            await update.message.reply_photo(photo=image_url, caption=caption, parse_mode="Markdown")
        
        await update.message.reply_audio(audio=open(audio_file, 'rb'), title=title, performer=artist)
        
        await status.delete()
        if os.path.exists(audio_file):
            os.remove(audio_file)

    except Exception as e:
        await status.edit_text("❌ Ката кетти, кайра аракет кылыңыз.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
