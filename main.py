import os
import glob
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes
from threading import Thread
from flask import Flask
import yt_dlp
import google.generativeai as genai

TOKEN = "8558649634:AAHEqz0qKwSg46pcqme0D84pLsdAmVIe8p8"
# Сиздин чыныгы Google Gemini API ачкычыңыз кошулду
GEMINI_API_KEY = "AQ.Ab8RN6JshXCurhsX2M5RUxh_ErMRf9NnxswK8C-76GFPkl5seg"
ADMIN_USER = "@Argen_70"

genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction="Сен жардамчы ботсуң. Жоопторду абдан так, түшүнүктүү, абзацтарга бөлүп жана ар бир сүйлөмгө же ойго тиешелүү сонун эмодзилерди кошуп кыргыз тилинде жаз."
)

app = Flask('')
@app.route('/')
def home(): return "Бот иштеп жатат!"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))

search_cache = {}
ai_active_users = set()

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

async def ask_ai(prompt_text):
    try:
        response = gemini_model.generate_content(prompt_text)
        return response.text.strip()
    except Exception as e:
        return f"⚠️ AI менен байланышууда ката кетти: {e}"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in ai_active_users:
        ai_active_users.remove(user_id)
        
    keyboard = [
        ["🤖 AI менен сүйлөшүү"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    text = (
        "👋 Салам! Мен музыка жана жардамчы ботмун.\n\n"
        "🎵 ыр издөө үчүн: трек [аты] же ыр [аты] деп жазыңыз.\n"
        "🤖 AI менен баарлашуу үчүн төмөнкү кнопканы басыңыз 👇\n\n"
        f"ℹ️ Бот Арген тарабынан түзүлгөн. Эгерде сурооңуз болсо, биздин админге кайрылсаңыз болот: {ADMIN_USER}"
    )
    
    await update.message.reply_text(text, reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    query = update.message.text
    if not query: return
    
    if query == "🤖 AI менен сүйлөшүү":
        ai_active_users.add(user_id)
        keyboard = [["❌ AI режимин өчүрүү"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "✨ AI баарлашуу режими ийгиликтүү күйгүзүлдү! 🤖\n\n"
            "💬 Эми мага каалаган сурооңузду бериңиз, мен сизге эмодзилер менен толук жооп беремин.",
            reply_markup=reply_markup
        )
        return

    if query == "❌ AI режимин өчүрүү":
        if user_id in ai_active_users:
            ai_active_users.remove(user_id)
        keyboard = [["🤖 AI менен сүйлөшүү"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "🛑 AI режими өчүрүлдү.\n\n"
            "🎵 Эми кайрадан музыка издей берсеңиз болот (трек [аты]).",
            reply_markup=reply_markup
        )
        return

    if user_id in ai_active_users:
        status_ai = await update.message.reply_text("🤖 Ойлонууда...")
        answer = await ask_ai(query)
        await status_ai.delete()
        await update.message.reply_text(answer)
        return

    lower_query = query.lower()
    if lower_query.startswith("трек ") or lower_query.startswith("ыр "):
        search_query = query[4:].strip() if lower_query.startswith("трек ") else query[3:].strip()
        
        status_msg = await update.message.reply_text("🔎 SoundCloud'дан изделүүдө...")
        
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
                keyboard = [[InlineKeyboardButton("🎵 Жүктөп алуу", callback_data="download_track")]]
                text = f"🎧 Табылды (SoundCloud):\n\n🔹 {track_info['title']}"
                
                await status_msg.delete()
                if track_info.get('thumbnail'):
                    await update.message.reply_photo(photo=track_info['thumbnail'], caption=text, reply_markup=InlineKeyboardMarkup(keyboard))
                else:
                    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
                return
        except:
            await status_msg.edit_text("❌ Көрсөтүлгөн ыр же трек табылган жок.")
            return

    await update.message.reply_text(
        "💡 Музыка издөө үчүн башына 'трек [аты]' же 'ыр [аты]' деп жазыңыз.\n\n"
        "🤖 Же '🤖 AI менен сүйлөшүү' кнопкасын басып маектешиңиз.\n\n"
        f"ℹ️ Админ: {ADMIN_USER}"
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    track = search_cache.get(query.from_user.id)
    if not track:
        await query.message.reply_text("⚠️ Ката чыкты, кайра издеңиз.")
        return

    status_msg = await query.message.reply_text(f"⏳ Жүктөлүүдө: {track['title']}...")
    
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
                await query.message.reply_audio(audio=f, title=track['title'], caption=f"👑 Admin: {ADMIN_USER}")
            
            os.remove(file_path)
            await status_msg.delete()
    except Exception as e:
        for f in glob.glob("temp_audio.*"): 
            try: os.remove(f)
            except: pass
        await status_msg.edit_text("❌ Жүктөөдө ката кетти.")

if __name__ == "__main__":
    Thread(target=run).start()
    bot = ApplicationBuilder().token(TOKEN).build()
    bot.add_handler(CommandHandler("start", start_command))
    bot.add_handler(CallbackQueryHandler(button_callback))
    bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    bot.run_polling()
