import asyncio
import logging
import os
import random
import re
from aiogram import Bot, Dispatcher, F, types
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from yt_dlp import YoutubeDL

TOKEN = "8797849312:AAEMEvV-WydOdGwElCEzIH44MHpDhvYGmgw"
ADMIN_ID = 7978591176

bot = Bot(token=TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

active_users = set()
user_modes = {}  # Колдонуучунун кайсы режимде экенин сактоо үшін ('soguu', 'jyly', 'erkel_qyz', 'erkel_bala')
user_genders = {} # Эркелетүү үчүн тандалган жыныс ('qyz' же 'bala')

# ================= БАЗАЛАР (ТОЛУК КЫРГЫЗЧА ЖАНА КӨП СӨЗДӨР) =================

proactive_phrases = [
    "Эй бир тууганым, кел майектешели, сүйлөшөлү! Абалың кандай, жакшысыңбы? Сени күтөм! 😊",
    "Кайда жүрөсүң, алтыным? Зеригип кеттим го, кел баарлашалы! ✨",
    "Эй досум, чарчаган жоксуңбу? Кел бир аз сүйлөшүп эс алалы! ☕️",
    "Жашоолор кандай болуп жатат, бир тууганым? Жаңылыктардан айтчы! 🚀",
    "Сени ойлоп отургам, кандай жүрөсүң? Кел баарлашалы! 🌟",
    "Эй тууган, дайынсыз болуп кеттиң го! Абалың жакшыбы? 🤝"
]

# 1. Согунуу сөздөрү (абдан көп варианттар)
soguu_words = [
    "Эй котагымды жебечи, сенин энеңдин амын тешип кетейин, мал неме! 😂 🖕",
    "Энеңди сагындыңбы өңүңдө, сенин котогуңду оозуңа тыгып, катуу сигем! 😆 👊",
    "Оозуңа карап сүйлө, сенин бүт тукумуңдун амын сыйрып салайын, тескери эшек! 😂 😈",
    "Жаман сөз жазсаң сени өзүм оозго алып катуу сигем! Ха-ха-ха, мал! 🤪 🖕",
    "Эй сенин мээң иштебей калганбы же тукумуң менен ошондойсуңбу? Котогумду жечи ары! 🤬",
    "Тилиң кычышып жатабы? Анда келип энеңдин амын жытта, иттин баласы! 😂🖕",
    "Эй шүмшүк, оозуңду жаппасаң азыр энеңди оозго алып салайын! 🖕",
    "Келчи бери, котогумду соруп койчу бир аз, эшек мал! 😆",
    "Сенин мээң жок кийиз экен го, мал башың менен эмне тыпылдайсың? 🤬",
    "Энеңди алайын, оозуңа коток тыгып койсо тынч болосуңбу, келесоо? 😂"
]

# 2. Жылуу мамиле сөздөрү (абдан көп варианттар)
jyly_words = [
    "Оо, жаным, абалың кандай? Күнүң абдан сонун өтүп жатабы? Сени көрүргө кубанычтамын! 🥰",
    "Алтыным, ар дайым жүзүңдөн жылмаюу кетпесин. Сен абдан жакшы адамсың! 🌟",
    "Салам бир тууганым! Баары жакшы болоруна ишенем, сенин колуңдан баары келет! 💪",
    "Жүрөгүң дайыма таза, жашооң сонун болсун! Кандай жардам керек? 🌸",
    "Сенин бүгүнкү маанайың сонун болсун деп каалайм! Ар дайым аман бол! ✨",
    "Дүйнөдөгү эң жакшы нерселердин баары сага насип этсин, досум! 💐",
    "Келчи кучактап коёюн, чарчады окшойсуң бүгүн? Баары жакшы болот! 🤗",
    "Сенин бар болгонуң жакшы, ар дайым ушинтип жаркырап жүр! ☀️"
]

# 3. Эркелетүү — Кыз катары сөздөр (балаларга арналган)
erkel_qyz_words = [
    "Алтыным менин, капризним менчик балам! Сени абдан катуу сүйөм го, сулуучам менин! 🥰💕",
    "Келчи кучагыма, менин эң таттуу баланчатайым! Сени эч кимге бербейм! 💖",
    "Эркелегим келди сен жанымда болсоң, маңдайымдагы жалгыз падышам менин! 😘",
    "Жаным падышам, чарчадыңызбы? Келиңиз маңдайыңыздан сылап коёюн! ✨",
    "Эрке балакайым менин, сенин ошол күлүмсүрөгөнүңө баарын берет элем! 🌹",
    "Жүрөгүмдүн ээси, менин мээримдүү жана күчтүү балам, сени абдан катуу жакшы көрөм! 💋",
    "Таттуум менин, сенсиз бул дүйнө мага кызыксыз! Ар дайым жанымда бол! 💓"
]

# 4. Эркелетүү — Бала катары сөздөр (кыздарга же балдарга арналган жылуу эркелетүүлөр)
erkel_bala_words = [
    "Менин эр жүрөк баатырым, күчтүү канатым! Сени менен баары коркпостон жашай алат! 🦁💪",
    "Алтын балам, менин калканым, сенин аркаңда тоодой болуп турамын! 🔥",
    "Менин таттуу эрке балам, капризденбей койчу анан сени катуу кучактап алайын! 🫂",
    "Келечегимдин ээси, менин күчтүү бүркүтүм, ийгиликтер дайыма коштосун сени! 🦅",
    "Менин алтын жигитим, сенин жылмаюуң бүт дүйнөнү жылытат! Жан дүйнөм кубанып турат! ✨",
    "Эрке макамым менин, сен абдан сонун адамсың, чарчасаң мен бармын жаныңда! 👑",
    "Менин таянычым, мырзам менин, сени абдан сыйлайм жана сүйөм! 💫"
]

# ================= КЛАВИАТУРАЛАР =================

def get_main_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="🤬 Согунуу"))
    builder.row(types.KeyboardButton(text="🥰 Жылуу мамиле"))
    builder.row(types.KeyboardButton(text="🤗 Эркелетүү"))
    builder.row(types.KeyboardButton(text="🛑 Токтотуу / Башынан"))
    return builder.as_markup(resize_keyboard=True)

def get_gender_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="👧 Кыз болом (Эркелетүү)", callback_data="gender_qyz"),
        types.InlineKeyboardButton(text="👦 Бала болом (Эркелетүү)", callback_data="gender_bala")
    )
    return builder.as_markup()

# ================= ФОНДУК БИРИНЧИ ЖАЗУУ =================

async def background_proactive_messenger():
    while True:
        await asyncio.sleep(random.randint(180, 400))
        for user_id in list(active_users):
            try:
                phrase = random.choice(proactive_phrases)
                await bot.send_message(user_id, phrase, reply_markup=get_main_keyboard())
            except Exception:
                pass

# ================= ХЕНДЛЕРЛЕР =================

@dp.message(F.text.casefold().in_(["/start", "start", "🛑 токтотуу / башынан", "токтотуу"]))
async def cmd_start(message: types.Message):
    user = message.from_user
    user_id = user.id
    active_users.add(user_id)
    user_modes[user_id] = None
    
    user_name = user.full_name
    username_str = f"@{user.username}" if user.username else "Юзернейми жок"
    
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

    welcome_text = (
        f"<b>Саламатсызбы, {user_name}!</b> Ботко кош келиңиз!\n\n"
        "Төмөнкү кнопкалардын бирин тандап сүйлөшүңүз:\n"
        "• <b>🤬 Согунуу</b> — Бот катуу согунуп жооп берет.\n"
        "• <b>🥰 Жылуу мамиле</b> — Жылуу, жакшы сөздөр.\n"
        "• <b>🤗 Эркелетүү</b> — Кыз же бала болуп эркелетет.\n"
        "• <i>Музыка үчүн:</i> <b>трек [ырдын аты]</b> деп жазыңыз."
    )
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )

@dp.message(F.text.casefold() == "🤬 согунуу")
async def set_mode_soguu(message: types.Message):
    user_modes[message.from_user.id] = "soguu"
    await message.answer("😈 Согунуу режимин күйгүздүң! Эми мага каалаган сөзүңдү жаз, көрөбүз кимибиз сөгүнөөр экенбиз! 😂", reply_markup=get_main_keyboard())

@dp.message(F.text.casefold() == "🥰 жылуу мамиле")
async def set_mode_jyly(message: types.Message):
    user_modes[message.from_user.id] = "jyly"
    await message.answer("🌸 Жылуу мамиле режимин күйгүздүң. Жаныңда ар дайым колдоого даяр сезимтал досуң бар! Жакшы сөздөрдү сүйлөшөлү.", reply_markup=get_main_keyboard())

@dp.message(F.text.casefold() == "🤗 эркелетүү")
async def set_mode_erkelotuu(message: types.Message):
    await message.answer("👇 Ким болуп эркелетейин? Төмөндөн бирин танда:", reply_markup=get_gender_keyboard())

@dp.callback_query(F.data.startswith("gender_"))
async def process_gender(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    active_users.add(user_id)
    
    if callback.data == "gender_qyz":
        user_modes[user_id] = "erkel_qyz"
        await callback.message.edit_text("👧 Кыз режимин тандадыңыз! Эми менин эркелеткич сөздөрүмдү кабыл алып туруңуз 💕")
    elif callback.data == "gender_bala":
        user_modes[user_id] = "erkel_bala"
        await callback.message.edit_text("👦 Бала режимин тандадыңыз! Эми сизди эркелетип, тоодой колдоп турамын 💪")
    
    await callback.answer()

# --- МУЗЫКА ИЗДӨӨ ---
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
        await message.answer("❌ Ырдын атын так жазыңыз.", reply_markup=get_main_keyboard())
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

# --- ТАНДАЛГАН РЕЖИМГЕ ЖАРАША ЖОП БЕРҮҮ ---
@dp.message()
async def handle_user_messages(message: types.Message):
    if not message.text:
        return
    
    user_id = message.from_user.id
    active_users.add(user_id)

    mode = user_modes.get(user_id)

    if mode == "soguu":
        reply = random.choice(soguu_words)
    elif mode == "jyly":
        reply = random.choice(jyly_words)
    elif mode == "erkel_qyz":
        reply = random.choice(erkel_qyz_words)
    elif mode == "erkel_bala":
        reply = random.choice(erkel_bala_words)
    else:
        reply = "Сураныч, төмөнкү баскычтардын бирин басып режимди тандаңыз же <b>трек [аты]</b> деп музыка издеңиз! 😊"

    await message.answer(reply, parse_mode="HTML", reply_markup=get_main_keyboard())

async def main():
    asyncio.create_task(background_proactive_messenger())
    print("Бот ийгиликтүү иштеди!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
