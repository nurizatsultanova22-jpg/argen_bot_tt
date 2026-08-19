import os
import glob
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes
from threading import Thread
from flask import Flask
import yt_dlp

TOKEN = "8558649634:AAHEqz0qKwSg46pcqme0D84pLsdAmVIe8p8"
ADMIN_USER = "@Argen_70"

app = Flask('')
@app.route('/')
def home(): return "Бот иштеп жатат! 🚀"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))

search_cache = {}

YDL_OPTS_SEARCH = {
    'default_search': 'scsearch1',
    'quiet': True,
    'extract_flat': True,
    'http_headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
}

YDL_OPTS_DOWNLOAD = {
    'format': 'bestaudio/best',
    'outtmpl': 'temp_audio.%(ext)s',
    'quiet': True,
    'noplaylist': True,
    'http_headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
}

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🔥 Популярдуу тректер (ТОП-10) 🌟"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    text = (
        "✨ Салам! Мен сиздин жеке музыкалык ботуңузмун! 🎵🤖\n\n"
        "🎧 Каалаган ырдын атын түздөн-түз жазып, заматта издеп алыңыз! ⚡️\n"
        "🔥 Же төмөнкү кнопканы басып, акыркы хит популярдуу тректерди тандаңыз 👇\n\n"
        f"👑 Админ: {ADMIN_USER} 💻"
    )
    await update.message.reply_text(text, reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    query = update.message.text
    if not query: return
    
    if query == "🔥 Популярдуу тректер (ТОП-10) 🌟":
        keyboard = [
            [InlineKeyboardButton("🎵 Хамдам - Жаңы ыр", callback_data="pop_1")],
            [InlineKeyboardButton("🎵 Bakr - Мадина", callback_data="pop_2")],
            [InlineKeyboardButton("🎵 ALHAM - Хикаям", callback_data="pop_3")],
            [InlineKeyboardButton("🎵 Jah Khalib - Лейла", callback_data="pop_4")],
            [InlineKeyboardButton("🎵 Miyagi & Andy Panda - Minor", callback_data="pop_5")],
            [InlineKeyboardButton("🎵 Macan - Aspergillus", callback_data="pop_6")],
            [InlineKeyboardButton("🎵 Xcho - Вороны", callback_data="pop_7")],
            [InlineKeyboardButton("🎵 Instasamka - За деньги нет", callback_data="pop_8")],
            [InlineKeyboardButton("🎵 Gayazovs Brothers - Малиновая Лада", callback_data="pop_9")],
            [InlineKeyboardButton("🎵 Баста - Сансара", callback_data="pop_10")]
        ]
        await update.message.reply_text("🔥 Учурда трендде жана дүүлүктүргөн ТОП-10 тректер: 🎧✨", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    search_query = query.strip()
    status_msg = await update.message.reply_text("🔍 SoundCloud базасынан тез изделүүдө... ⏳")
    
    try:
        with yt_dlp.YoutubeDL(YDL_OPTS_SEARCH) as ydl:
            res = ydl.extract_info(f"scsearch1:{search_query}", download=False)
            entries = res.get('entries', [])
            if not entries:
                raise Exception("Табылган жок")
            
            entry = entries[0]
            track_info = {
                'title': entry.get('title', search_query),
                'url': entry.get('url'),
                'thumbnail': entry.get('thumbnail')
            }
            
            search_cache[user_id] = track_info
            keyboard = [[InlineKeyboardButton("📥 Аудиону жүктөө 🎵", callback_data="download_track")]]
            text = f"🎧 **Ийгиликтүү табылды!** ✨\n\n🔹 **{track_info['title']}** 🎶"
            
            await status_msg.delete()
            if track_info.get('thumbnail'):
                await update.message.reply_photo(photo=track_info['thumbnail'], caption=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
            else:
                await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
            return
    except:
        await status_msg.edit_text("❌ Тилекке каршы, бул ыр табылган жок. Башка атын жазып көрүңүзчү! 🔍✨")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data.startswith("pop_"):
        songs = {
            "pop_1": "Хамдам",
            "pop_2": "Bakr Madina",
            "pop_3": "ALHAM Hikayam",
            "pop_4": "Jah Khalib Лейла",
            "pop_5": "Miyagi Minor",
            "pop_6": "Macan Asphalt",
            "pop_7": "Xcho Вороны",
            "pop_8": "Instasamka За деньги нет",
            "pop_9": "Gayazovs Brothers Малиновая Лада",
            "pop_10": "Баста Сансара"
        }
        search_query = songs.get(data, "Hit music")
        status_msg = await query.message.reply_text("⚡️ Тандалган трек өтө тез изделүүдө... ⏳")
        
        try:
            with yt_dlp.YoutubeDL(YDL_OPTS_SEARCH) as ydl:
                res = ydl.extract_info(f"scsearch1:{search_query}", download=False)
                entries = res.get('entries', [])
                if not entries: raise Exception()
                
                entry = entries[0]
                track_info = {
                    'title': entry.get('title', search_query),
                    'url': entry.get('url'),
                    'thumbnail': entry.get('thumbnail')
                }
                search_cache[query.from_user.id] = track_info
                keyboard = [[InlineKeyboardButton("📥 Аудиону жүктөө 🎵", callback_data="download_track")]]
                text = f"🔥 **Тренддеги трек табылды!** 🌟\n\n🔹 **{track_info['title']}** 🎶"
                
                await status_msg.delete()
                if track_info.get('thumbnail'):
                    await query.message.reply_photo(photo=track_info['thumbnail'], caption=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
                else:
                    await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
                return
        except:
            await status_msg.edit_text("❌ Ката кетти, сураныч кайра аракет кылыңыз! ⚠️")
            return

    track = search_cache.get(query.from_user.id)
    if not track:
        await query.message.reply_text("⚠️ Сессия эскирди, сураныч ырды кайра издеңиз! 🔄")
        return

    status_msg = await query.message.reply_text(f"⏳ **{track['title']}** телефонго жогорку ылдамдыкта жүктөлүүдө... 🚀")
    
    for f in glob.glob("temp_audio.*"): 
        try: os.remove(f)
        except: pass

    try:
        with yt_dlp.YoutubeDL(YDL_OPTS_DOWNLOAD) as ydl:
            ydl.extract_info(track['url'], download=True)
            downloaded = glob.glob("temp_audio.*")
            if not downloaded:
                raise Exception("Файл табылган жок")
            
            file_path = downloaded[0]
            
            with open(file_path, 'rb') as f:
                await query.message.reply_audio(audio=f, title=track['title'], caption=f"👑 Түзүүчү: {ADMIN_USER} ✨🎧")
            
            os.remove(file_path)
            await status_msg.delete()
    except Exception as e:
        for f in glob.glob("temp_audio.*"): 
            try: os.remove(f)
            except: pass
        await status_msg.edit_text("❌ Жүктөө учурунда ката кетти. Кайра баскып көрүңүз! ⚠️")

if __name__ == "__main__":
    Thread(target=run).start()
    bot = ApplicationBuilder().token(TOKEN).build()
    bot.add_handler(CommandHandler("start", start_command))
    bot.add_handler(CallbackQueryHandler(button_callback))
    bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    bot.run_polling()
