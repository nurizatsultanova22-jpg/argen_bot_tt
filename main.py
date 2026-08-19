import os
import random
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = "8558649634:AAHEqz0qKwSg46pcqme0D84pLsdAmVIe8p8"

# Согунган сөздөр тизмеси
BANNED_WORDS = ["дурак", "бля", "орой_соз1"] 

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    welcome_text = (
        f"🌟 **Салам, {user_name}!**\n\n"
        "Мен Аргендин профессионалдык музыкалык ботумун. 🎧\n"
        "Мага ырдын атын жазыңыз, мен аны Deezer базасынан таап, сизге аудио трек катары жөнөтөм! 🚀\n\n"
        "🔘 /game - Көңүл ачуу үчүн оюн\n"
        "🔘 /help - Жардам"
    )
    keyboard = [[InlineKeyboardButton("🎵 Издөөнү баштоо", callback_data="search_hint")]]
    await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

# Музыка издөө жана жөнөтүү логикасы
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    
    # Согунган сөздөрдү текшерүү
    for word in BANNED_WORDS:
        if word in text:
            await update.message.reply_text("🛑 Досум, адептүү бололу! Жакшы музыка угалы. 😊")
            return

    status = await update.message.reply_text("🔍 Ыр изделүүдө...")
    
    try:
        url = f"https://api.deezer.com/search?q={update.message.text}"
        response = requests.get(url).json()
        tracks = response.get('data', [])
        
        if not tracks:
            await status.edit_text("❌ Кечиресиз, ыр табылган жок.")
            return

        track = tracks[0]
        title = track['title']
        artist = track['artist']['name']
        audio_url = track['preview']
        image_url = track['album']['cover_big']
        youtube_link = f"https://www.youtube.com/results?search_query={artist}+{title}".replace(" ", "+")

        # Дизайндык жооп
        caption = (
            f"🎵 **{artist} - {title}**\n\n"
            f"👤 Колдонуучу: @Argen\n"
            f"🔗 [YouTube'дан угуу]({youtube_link})"
        )
        
        # Сүрөт менен аудиону бирге жөнөтүү
        await update.message.reply_photo(photo=image_url, caption=caption, parse_mode="Markdown")
        await update.message.reply_audio(audio=audio_url, title=title, performer=artist)
        await status.delete()

    except Exception:
        await status.edit_text("⚠️ Ката кетти, кайра аракет кылыңыз.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(lambda u, c: u.callback_query.message.reply_text("🎤 Ырдын атын жазыңыз:")))
    print("Бот иштеп жатат...")
    app.run_polling()
