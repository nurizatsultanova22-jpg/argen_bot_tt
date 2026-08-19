import os
import sqlite3
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    filters,
    ContextTypes,
)

TOKEN = "8558649634:AAHEqz0qKwSg46pcqme0D84pLsdAmVIe8p8"

# Жөнөтүүчү админдин ID радары (өзүңүздүн Telegram ID'ңизди же бот автоматтык тааныган логика)
# Админ ботко "/admin" деп жазганда автоматтык түрдө базага админ болуп сакталат.

# 1. Базаны түзүү (База данных)
def init_db():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    # Катталуучулар таблицасы
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY
        )"""
    )
    # Медиа базасы (ыр, видео, сүрөт сактоо үчүн)
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS media_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT,
            file_type TEXT,
            caption TEXT
        )"""
    )
    # Админдер таблицасы
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS admins (
            admin_id INTEGER PRIMARY KEY
        )"""
    )
    conn.commit()
    conn.close()

init_db()

# Админ болоор/текшерүүчү функция
def is_admin(user_id):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admins WHERE admin_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res is not None

# Старт командасы (Кош келдиң бүткөн жер)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Колдонуучуну базага каттайбыз
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

    welcome_text = (
        "✨ *Добро пожаловать в наш музыкальный мир!* 🎧\n\n"
        "🖤 Здесь ты найдешь лучший вайб, крутые треки и атмосферу.\n"
        "Отправь название трека или наслаждайся контентом!"
    )
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)

# Админ болуу үчүн команда (/admin)
async def make_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    
    # Эгер админдер таблицасы бош болсо, биринчи жазган киши автоматтык түрдө бас админ болот!
    cursor.execute("SELECT COUNT(*) FROM admins")
    count = cursor.fetchone()[0]
    
    if count == 0 or not is_admin(user_id):
        cursor.execute("INSERT OR IGNORE INTO admins (admin_id) VALUES (?)", (user_id,))
        conn.commit()
        conn.close()
        await update.message.reply_text("👑 *Поздравляю! Теперь ты главный администратор этого бота.*", parse_mode=ParseMode.MARKDOWN)
    else:
        conn.close()
        await update.message.reply_text("⚡ *Ты уже зарегистрирован как администратор.*", parse_mode=ParseMode.MARKDOWN)

# Администратор контент жөнөткөндө (Сүрөт, Видео, Аудио) базага сактоо жана таратуу
async def handle_admin_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ *У тебя нет прав администратора для загрузки контента.*", parse_mode=ParseMode.MARKDOWN)
        return

    message = update.message
    file_id = None
    file_type = None
    original_caption = message.caption or message.text or ""

    if message.audio:
        file_id = message.audio.file_id
        file_type = "audio"
    elif message.video:
        file_id = message.video.file_id
        file_type = "video"
    elif message.photo:
        file_id = message.photo[-1].file_id
        file_type = "photo"

    if file_id:
        # Базага сактоо жана Астына "Папкалар / Ырлар" стилин кошуу
        styled_caption = f"📁 *Папки / Музыка*\n\n{original_caption}\n\n👤 *By Argen*"
        
        conn = sqlite3.connect("bot_database.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO media_posts (file_id, file_type, caption) VALUES (?, ?, ?)",
            (file_id, file_type, styled_caption),
        )
        post_id = cursor.lastrowid
        conn.commit()
        conn.close()

        await message.reply_text(
            f"✅ *Контент успешно сохранен в базу под номером #{post_id}!*\n"
            f"Отправь команду `/send {post_id}` чтобы разослать это всем подписчикам.",
            parse_mode=ParseMode.MARKDOWN,
        )

# Рассылка кылуу функциясы (+ же /send ID аркылуу)
async def broadcast_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        return

    if not context.args:
        await update.message.reply_text("⚠️ *Укажи ID поста для рассылки. Пример: `/send 1`*", parse_mode=ParseMode.MARKDOWN)
        return

    post_id = context.args[0]

    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT file_id, file_type, caption FROM media_posts WHERE id = ?", (post_id,))
    post = cursor.fetchone()

    if not post:
        conn.close()
        await update.message.reply_text("❌ *Пост с таким ID не найден в базе.*", parse_mode=ParseMode.MARKDOWN)
        return

    file_id, file_type, caption = post

    # Бардык катталуучуларды алабыз
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    conn.close()

    success_count = 0
    status_msg = await update.message.reply_text("⏳ *Рассылка началась...*", parse_mode=ParseMode.MARKDOWN)

    for (u_id,) in users:
        try:
            if file_type == "audio":
                await context.bot.send_audio(chat_id=u_id, audio=file_id, caption=caption, parse_mode=ParseMode.MARKDOWN)
            elif file_type == "video":
                await context.bot.send_video(chat_id=u_id, video=file_id, caption=caption, parse_mode=ParseMode.MARKDOWN)
            elif file_type == "photo":
                await context.bot.send_photo(chat_id=u_id, photo=file_id, caption=caption, parse_mode=ParseMode.MARKDOWN)
            success_count += 1
        except Exception:
            pass # Эгер колдонуучу ботту өчүрсө ката бербеши үчүн

    await status_msg.edit_text(f"✅ *Рассылка успешно завершена! Получателей:* {success_count}", parse_mode=ParseMode.MARKDOWN)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", make_admin))
    app.add_handler(CommandHandler("send", broadcast_post))
    
    # Админ медиа жөнөткөндө кармап калуучу фильтр
    app.add_handler(MessageHandler(filters.AUDIO | filters.VIDEO | filters.PHOTO, handle_admin_media))

    print("🔥 Бот с базой данных и админ-панелью запущен!")
    app.run_polling()
