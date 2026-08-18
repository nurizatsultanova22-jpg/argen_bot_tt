import os
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes
from threading import Thread
from flask import Flask
import yt_dlp

# Админ маалыматы сакталды
TOKEN = "8558649634:AAHEqz0qKwSg46pcqme0D84pLsdAmVIe8p8"
ADMIN_USER = "@Argen_70"

app = Flask('')
@app.route('/')
def home(): return "Бот иштейт!"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))

search_cache = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🎧 Салам! Кайсы ырды уккуң келет?\n\n"
        "🚀 YouTube жана SoundCloud'дан ырларды тез издейм.\n"
        "🔍 Жөн гана ырдын атын жазып жибер.\n\n"
        f"👑 Админ: {ADMIN_USER}"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text or ""
    
    query = text
    if text.lower().startswith("трек "):
        query = text[5:].strip()
    elif text.lower().startswith("найти "):
        query = text[6:].strip()

    status_msg = await update.message.reply_text("⚡ Ырларды издеп жатам... 🔍")
    
    ydl_opts = {
        'format': 'bestaudio',
        'quiet': True,
    }
    
    try:
        entries = []
        # YouTube'дан издөө
        try:
            with yt_dlp.YoutubeDL({**ydl_opts, 'default_search': 'ytsearch3'}) as ydl:
                res = ydl.extract_info(f"ytsearch3:{query}", download=False)
                if 'entries' in res: entries.extend(res['entries'])
        except: pass

        # SoundCloud'дан издөө
        try:
            with yt_dlp.YoutubeDL({**ydl_opts, 'default_search': 'scsearch3'}) as ydl:
                res = ydl.extract_info(f"scsearch3:{query}", download=False)
                if 'entries' in res: entries.extend(res['entries'])
        except: pass

        if not entries:
            await status_msg.edit_text("❌ Кечиресиз, ыр табылган жок.")
            return

        entries = entries[:5]
        search_cache[user.id] = entries
        
        response_text = "🎵 **Табылган варианттар:**\n\n"
        keyboard = []
        row = []
        for i, entry in enumerate(entries, 1):
            title = entry.get('title', 'Музыка')
            response_text += f"**{i}.** {title}\n"
            row.append(InlineKeyboardButton(str(i), callback_data=f"select_{i-1}"))
        keyboard.append(row)

        await status_msg.edit_text(response_text + f"\n👑 Админ: {ADMIN_USER}", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        
    except Exception as e:
        await status_msg.edit_text("❌ Издөө учурунда ката кетти.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if query.data.startswith("select_"):
        index = int(query.data.split("_")[1])
        entries = search_cache.get(user_id)
        if not entries or index >= len(entries):
            await query.message.edit_text("⚠️ Убакыт өтүп кетти, кайра издеңиз.")
            return

        selected = entries[index]
        url = selected.get('webpage_url') or selected.get('url')
        title = selected.get('title', 'Музыка')
        
        status_msg = await query.message.reply_text(f"📥 Жүктөлүүдө: {title} ⏳")

        try:
            with yt_dlp.YoutubeDL({'format': 'bestaudio', 'quiet': True, 'outtmpl': 'song.mp3'}) as ydl:
                ydl.download([url])

            caption_text = f"🎵 {title}\n\n✨ Жагымдуу угуу!\n👑 Админ: {ADMIN_USER}"
            with open("song.mp3", 'rb') as audio:
                await context.bot.send_audio(chat_id=query.message.chat_id, audio=audio, title=title, caption=caption_text)
            await status_msg.delete()
            if os.path.exists("song.mp3"): os.remove("song.mp3")
        except:
            await status_msg.edit_text("❌ Файлды жүктөөдө ката кетти.")

if __name__ == "__main__":
    Thread(target=run).start()
    bot = ApplicationBuilder().token(TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CallbackQueryHandler(button_callback))
    bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    bot.run_polling()
