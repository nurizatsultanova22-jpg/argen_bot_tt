import asyncio
import logging
import os
import random
import re
from aiogram import Bot, Dispatcher, F, types
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from yt_dlp import YoutubeDL

TOKEN = "8797849312:AAEMEvV-WydOdGwElCEzIH44MHpDhvYGmgw"
ADMIN_ID = 7978591176  # Сиздин админ ID

bot = Bot(token=TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

active_users = set()
trolling_users = set()

# Өз алдынча зеригип калганда биринчи жазуучу билдирүүлөр
proactive_phrases = [
    "Эй шүмшүк, кел зериктинби, азыр сөгүшөбүзбү же сүйлөшөбүзбү? 😈🖕",
    "Эй мал, чего замолчал? Испугался или как? Давай пообщаемся! 🤬",
    "Эй келесоо, жаман зерикдим, кайсы тешикке кирип кеттиң? 🗣️",
]

def get_adaptive_reply(text: str) -> str:
    t = text.lower()
    is_russian = any(char in t for char in "абвгдеёжзийклмнопрстуфхцчшщъыьэюя")
    
    # Негатив / Согунүү сөздөрү жазылса — катуу жооп жана күлгөн смайлик
    bad_words_kg = ["котогум", "амың", "энең", "ам", "сойлап", "коток", "шалава", "блять", "сука", "нахуй", "пидор", "сигем"]
    bad_words_ru = ["сука", "блять", "хуй", "пидор", "ебать", "залупа", "мразь", "урод", "шлюха", "гондон"]
    
    if any(w in t for w in bad_words_kg) or any(w in t for w in bad_words_ru):
        if is_russian:
            return random.choice([
                "Ты чё охерел, мразь? Я тебя сам сейчас так выебу, мало не покажется! 😂 😈",
                "Соси хуй, урод! Хули ты тут быкуешь, я тебя быстрее сгною! 😆 🖕",
                "Ха-ха, рот свой прикрой петух! Сигем сени өзүм! 😂 🤬"
            ])
        else:
            return random.choice([
                "Эй котагымды жебечи, сенин энеңди сигем, мал неме! 😂 🖕",
                "Жаман сөз жазсаң сени өзүм оозго алып сигем! Ха-ха-ха! 😆 👊",
                "Котогумду жеп калыптырсың, сени катуу эле сигем! 😂 😈"
            ])

    # Жакшы сөздөр / Саламдашуулар
    if any(w in t for w in ["салам", "куш", "привет", "жакшы", "кандай", "дос", "брат", "красавчик", "как дела"]):
        if is_russian:
            return random.choice([
                "Здорово, братуха! Очень рад тебя слышать, красавчик! 😎👊",
                "Всё отлично! Сам как поживаешь, чё нового? ✨"
            ])
        else:
            return random.choice([
                "Оо, брат, өзүң кандай жатасың? Күнүң сонун өтүп жатабы? 😎👊",
                "Жакшы шүгүр, өзүңдү карап койчу, баары сонун болсун! ✨"
            ])

    # Башка сөздөргө жооп
    if is_russian:
        return random.choice([
            "Интересно ты рассуждаешь, но давай по делу. 🥱",
            "Очередной бред выдал. Иди лучше музычку послушай! 🎵"
        ])
    else:
        return random.choice([
            "Эй мал, эмне деп күңкүлдөп жатасың? Мээң катып калганбы? 🧠",
            "Котогумду жебей тынч отурчу! 💩"
        ])

def get_main_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="Старт слова"))
    builder.row(types.KeyboardButton(text="Стоп"))
    return builder.as_markup(resize_keyboard=True)

async def background_proactive_messenger():
    while True:
        await asyncio.sleep(random.randint(180, 400))
        for user_id in list(trolling_users):
            try:
                phrase = random.choice(proactive_phrases)
                await bot.send_message(user_id, phrase, reply_markup=get_main_keyboard())
            except Exception:
                pass

# --- ЖАҢЫ КОЛДОНУУЧУ КИРГЕНДЕ АДМИНГЕ КАТАРЛДЫ ДЕП ЖӨНӨТҮҮ ЖАНА ЖЫЛУУ ТОСУП АЛУУ ---
@dp.message(F.text.casefold().in_(["/start", "start"]))
async def cmd_start(message: types.Message):
    user = message.from_user
    user_id = user.id
    active_users.add(user_id)
    
    # Администраторго жаңы колдонуучу тууралуу кабар жөнөтүү (смайлик тазаланды)
    user_name = user.full_name
    username_str = f"@{user.username}" if user.username else "Колдонуучунун юзернейми жок"
    
    admin_notification = (
        f"<b>Жаңы колдонуучу катталды!</b>\n\n"
        f"👤 Аты: {user_name}\n"
        f"🔗 Юзернейми: {username_str}\n"
        f"🆔 ID: <code>{user_id}</code>"
    )
    
    try:
        await bot.send_message(ADMIN_ID, admin_notification, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Админге кабар жөнөтүү катасы: {e}")

    # Колдонуучуну жылуу тосуп алуу
    welcome_text = (
        f"<b>Саламатсызбы, {user_name}!</b> Ботко кош келиңиз!\n\n"
        "Сизди көргөнүбүзгө абдан кубанычтабыз. Бул бот аркылуу сиз:\n"
        "• Музыка издей аласыз (<i>трек [ырдын аты]</i>)\n"
        "• Автоматтык түшүнүктүү маектешүү режимин күйгүзө аласыз («Старт слова» баскычы аркылуу)\n\n"
        "Жакшы жазсаңыз жакшы мамиле кылабыз, жаман сөз жазсаңыз жооп кайтаруудан качпайбыз! 😉 Жакшы маанай каалайбыз!"
    )
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )

# --- АДМИН РАССЫЛКА ---
@dp.message(F.from_user.id == ADMIN_ID, F.text.startswith("/send"))
async def admin_broadcast_media(message: types.Message):
    if not active_users:
        await message.answer("❌ В базе пока нет пользователей.")
        return

    broadcast_text = message.text[5:].strip()
    text_content = broadcast_text or message.caption or ""
    url_match = re.search(r'(https?://[^\s]+)', text_content)

    keyboard = None
    if url_match:
        found_url = url_match.group(1)
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🔗 Перейти", url=found_url))
        keyboard = builder.as_markup()

    success_count = 0
    fail_count = 0

    for user_id in active_users:
        if user_id == ADMIN_ID:
            continue
        try:
            if broadcast_text:
                await bot.send_message(
                    chat_id=user_id,
                    text=broadcast_text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            else:
                await bot.copy_message(
                    chat_id=user_id,
                    from_chat_id=message.chat.id,
                    message_id=message.message_id,
                    reply_markup=keyboard
                )
            success_count += 1
            await asyncio.sleep(0.05)
        except Exception:
            fail_count += 1

    await message.answer(
        f"📊 <b>Рассылка завершена!</b>\n\n"
        f"✅ Доставлено: {success_count}\n"
        f"❌ Ошибок: {fail_count}",
        parse_mode="HTML"
    )

@dp.message(F.text.casefold() == "старт слова")
async def start_troll(message: types.Message):
    trolling_users.add(message.from_user.id)
    await message.answer("😈 Автоматтык режим күйгүздү! Жакшы жазсаң жакшы, жаман сөз жазсаң сигем же катуу сөгүшөм! 😂 Жакшы маек курабыз.", reply_markup=get_main_keyboard())

@dp.message(F.text.casefold() == "стоп")
async def stop_troll(message: types.Message):
    user_id = message.from_user.id
    if user_id in trolling_users:
        trolling_users.remove(user_id)
        await message.answer("🛑 Автоматтык режим өчүрүлдү. Тыныгуу! 😊", reply_markup=get_main_keyboard())
    else:
        await message.answer("Режим и так өчүк эле.", reply_markup=get_main_keyboard())

# --- МУЗЫКА ИЗДӨӨ ЖАНА ЖӨНӨТҮҮ ---
@dp.message(F.text.casefold().startswith(("трек ", "найти ")))
async def search_and_send_music(message: types.Message):
    user_id = message.from_user.id
    active_users.add(user_id)

    text = message.text.strip()
    if text.lower().startswith("трек "):
        query = text[5:].strip()
    else:
        query = text[6:].strip()

    if not query:
        await message.answer("❌ Ырдын атын жазыңыз.", reply_markup=get_main_keyboard())
        return

    wait_msg = await message.answer("🔍 Музыка изделүүдө, күтө туруңуз...")

    ydl_opts = {
        'format': 'bestaudio/best',
        'default_search': 'scsearch1',
        'outtmpl': '%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'noplaylist': True,
        'quiet': True
    }

    file_path = None
    try:
        def download():
            with YoutubeDL(ydl_opts) as ydl:
                try:
                    info = ydl.extract_info(query, download=True)
                except Exception:
                    ydl.params['default_search'] = 'ytsearch1'
                    info = ydl.extract_info(query, download=True)

                if 'entries' in info:
                    info = info['entries'][0]
                
                title = info.get('title', 'Audio')
                safe_title = "".join([c for c in title if c.isalnum() or c.isspace() or c in "_-"]).strip()
                if not safe_title:
                    safe_title = "audio"
                
                mp3_path = f"{safe_title}.mp3"
                filename = ydl.prepare_filename(info)
                base, _ = os.path.splitext(filename)
                real_mp3 = base + '.mp3'
                
                if os.path.exists(real_mp3) and real_mp3 != mp3_path:
                    if os.path.exists(mp3_path):
                        os.remove(mp3_path)
                    os.rename(real_mp3, mp3_path)

                return title, mp3_path

        loop = asyncio.get_running_loop()
        title, file_path = await loop.run_in_executor(None, download)

        if file_path and os.path.exists(file_path):
            audio_file = types.FSInputFile(file_path, filename=f"{title}.mp3")
            caption_text = f"🎵 <b>{title}</b>\n\n@Argen_70"
            
            await message.answer_audio(
                audio=audio_file, 
                caption=caption_text,
                parse_mode="HTML",
                reply_markup=get_main_keyboard()
            )
        else:
            await wait_msg.edit_text("❌ Тилекке каршы, бул музыка табылган жок.", reply_markup=get_main_keyboard())
            return
        
        try:
            await wait_msg.delete()
        except Exception:
            pass

    except Exception:
        try:
            await wait_msg.edit_text("❌ Ката кетти, кийинчерээк кайра аракет кылыңыз.", reply_markup=get_main_keyboard())
        except Exception:
            pass
    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

@dp.message()
async def handle_troll_messages(message: types.Message):
    if not message.text:
        return
    
    user_id = message.from_user.id
    active_users.add(user_id)

    if user_id in trolling_users:
        reply_text = get_adaptive_reply(message.text)
        await message.answer(reply_text, reply_markup=get_main_keyboard())
    else:
        await message.answer("Ыр издөө үшін <b>«трек [аты]»</b> деп жазыңыз же <b>«Старт слова»</b> баскычын басыңыз.", parse_mode="HTML", reply_markup=get_main_keyboard())

async def main():
    asyncio.create_task(background_proactive_messenger())
    print("Бот ийгиликтүү иштеди!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
