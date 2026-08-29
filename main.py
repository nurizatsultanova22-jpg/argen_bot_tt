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
trolling_users = set()

# Бот зеригип калганда өзү биринчи жазуучу билдирүүлөр базасы (абдан көбөйтүлдү)
proactive_phrases = [
    "Эй шүмшүк, кел зериктинби, азыр энеңди оозго алып сөгүшөбүзбү же сүйлөшөбүзбү? 😈🖕",
    "Эй мал, чего замолчал? Испугался или как? Давай пообщаемся или посремося! 🤬",
    "Эй келесоо, жаман зерикдим, кайсы тешикке кирип кеттиң, давай поболтаем! 🗣️",
    "Эй бетпак, скучно стало же, давай поцапаемся или нормально поговорим? 🥱",
    "Алло, гараж! Ты живой вообще или тебя уже сожрали тараканы? 🪳",
    "Эй эшек, кайда жүрөсүң үн катпай? Кел бир нерсени талкуулайлы же сөгүшөлү! 🔥",
    "Эй достук, скучаешь по мне да? Признайся, без моих матов жизнь скучна! 😎",
    "Кайда жоголуп кеттиң, мал башың менен? Чык сыртка чаткылашабыз! 👊"
]

def get_adaptive_reply(text: str) -> str:
    t = text.lower()
    
    # Кыргызча тамгалар жана сөздөр аркылуу тилди так ажыратуу
    kg_specific_chars = ["ң", "ө", "ү", "ғ", "қ", "һ"]
    kg_words = ["салам", "кандай", "эмне", "жок", "ооба", "жакшы", "жаман", "котогум", "энең", "сигем", "кел", "кой", "амың", "билем", "айт", "қайда", "неме", "мал"]
    
    is_kyrgyz = any(char in t for char in kg_specific_chars) or any(w in t for w in kg_words)
    
    # Согунүү жана негатив сөздөрүн текшерүү
    bad_words_kg = ["котогум", "амың", "энең", "ам", "сойлап", "коток", "шалава", "блять", "сука", "нахуй", "пидор", "сигем", "эшек", "мал", "сом"]
    bad_words_ru = ["сука", "блять", "хуй", "пидор", "ебать", "залупа", "мразь", "урод", "шлюха", "гондон", "отсоси", "долбоёб", "сукин"]
    
    if any(w in t for w in bad_words_kg) or any(w in t for w in bad_words_ru):
        if not is_kyrgyz:
            return random.choice([
                "Ты чё охерел, мразь? Я твой рот и всю твою семью наизнанку выверну, кусок дерьма! 😂 🖕",
                "Соси хуй, урод! Твоя мамаша знатная шлюха, раз воспитала такого долбоёба! 😆 🤬",
                "Завали своё ебало, петух комнатный! Хули ты тут раскавкался, конченый? Я тебя сам выебу! 😂 😈",
                "Ты на кого пасть разеваешь, гнида тупорылая? Я тебя в порошок сотру и не подавлюсь! 🖕🔥",
                "Рот закрой свой, петушара! Ты чё возомнил о себе, утырок конченый? Сигем сени өзүм! 🤪"
            ])
        else:
            return random.choice([
                "Эй котагымды жебечи, сенин энеңдин амын тешип кетейин, мал неме! 😂 🖕",
                "Энеңди сагындыңбы өңүңдө, сенин котогуңду оозуңа тыгып, катуу сигем! 😆 👊",
                "Оозуңа карап сүйлө, сенин бүт тукумуңдун амын сыйрып салайын, тескери эшек! 😂 😈",
                "Жаман сөз жазсаң сени өзүм оозго алып катуу сигем! Ха-ха-ха, мал! 🤪 🖕",
                "Эй сенин мээң иштебей калганбы же тукумуң менен ошондойсуңбу? Котогумду жечи ары! 🤬",
                "Тилиң кычышып жатабы? Анда келип энеңдин амын жытта, иттин баласы! 😂🖕"
            ])

    # Жакшы сөздөр жана саламдашуулар (абдан кеңейтилди)
    if any(w in t for w in ["салам", "куш", "привет", "жакшы", "кандай", "дос", "брат", "красавчик", "как дела", "добрый", "здорово", "рахмат", "сонун"]):
        if not is_kyrgyz:
            return random.choice([
                "Здорово, братуха! Как сам, как жизнь молодая? Очень рад тебя слышать, красавчик! 😎👊",
                "Всё пучком! Сам как поживаешь, чё нового в мире творится? ✨",
                "Привет-привет! Рад слышать, чё хотел обсудить сегодня? 🤝",
                "Отлично всё! Рассказывай, какие планы на сегодня, бро? ✌️",
                "О, какие люди! Салют тебе, уважаемый, как настроение? 🌟",
                "Здарова! Жизнь бьёт ключом, и всё по голове, а у тебя как? 😉"
            ])
        else:
            return random.choice([
                "Оо, брат, өзүң кандай жатасың? Күнүң кандай өтүп жатат, баары сонунбу? 😎👊",
                "Жакшы шүгүр, өзүңдү карап койчу, чарчабай жүрөсүңбү? Жакшы жашоо! ✨",
                "Салам! Эмне жаңылык, баары жайындабы же дагы бир маселе чыктыбы? 🤝",
                "Өзүң жакшы болсоң, мен да сонунмун! Айта бер, бүгүн кандай пландар бар? ✌️",
                "Алоо, салам! Келгениң жакшы болду, маанай кандай өйдө жактабы? 🌟",
                "УИАУ! Салам досум, баары жайында, өзүң чарчабай аман жүрөсүңбү? ☕️"
            ])

    # Башка каалагандай миллиондогон сөздөргө нейтралдык же жооп кайтаруучу база
    if not is_kyrgyz:
        return random.choice([
            "Ты чё тут умничаешь сидишь, профессор диванный? Лучше расскажи что-нибудь интересное! 🥱",
            "Слушай, твои мысли — полная херня, но послушать тебя забавно. Давай по делу! 🤫",
            "Интересно ты рассуждаешь, но всем вообще похуй. Давай лучше музыку послушаем или поспорим! 🤡",
            "Очередной бред выдал. Иди лучше делом займись, эксперт комнатный, блять! 📉",
            "Я смотрю, у тебя язык без костей. Всё подряд молотишь, да? 🗣️",
            "Чё ты мне тут сказки рассказываешь? Лучше трек послушай или помолчи! 🎶"
        ])
    else:
        return random.choice([
            "Эй мал, эмне деп узун сабак күңкүлдөп жатасың, түшүнүктүүрөөк жазчы! Мээң катып калганбы? 🧠🧊",
            "Котогумду жегениң качан калат? Жөн эле отурчу тынч, же башка тема сүйлөшөлү! 💩",
            "Сенин башың кичине иштейби же толугу менен токмоктолуп калганбы, түшүндүрүп койчу? 🤡",
            "Тилиңди тишиңге тиштеп тынч отурбасаң, азыр энеңди оозго алып салайын! Түшүндүңбү? 🤬",
            "Эмнелерди гана жазбайсың ээ, мээни жедиң го толук! Башка нормальный нерсе жазчы. 🙄",
            "Сенин бул айткандарыңды угуп, өзүм эле оозго алып кете жаздадым. Башка соз таппай калдыўбы? 🤦‍♂️"
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

@dp.message(F.text.casefold().in_(["/start", "start"]))
async def cmd_start(message: types.Message):
    user = message.from_user
    user_id = user.id
    active_users.add(user_id)
    
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
        "Сизди көргөнүбүзгө абдан кубанычтабыз. Бул бот аркылуу сиз:\n"
        "• Музыка издей аласыз (<i>трек [ырдын аты]</i>)\n"
        "• Автоматтык маектешүү режимин күйгүзө аласыз («Старт слова» баскычы аркылуу)\n\n"
        "Жакшы жазсаңыз жакшы мамиле кылабыз, жаман сөз жазсаңыз катуу сөгүшүп сигем деп жооп кайтарабыз! 😉 Жакшы маанай каалайбыз!"
    )
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )

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
    await message.answer("😈 Автоматтык режим күйгүздү! Кыргызча жазсаңыз кыргызча, орусча жазсаңыз орусча сүйлөшөбүз. Жакшы жазсаңыз жакшы, жаман сөз жазсаңыз сигем же катуу сөгүшөм! 😂 Келиңиз, каткырып сүйлөшөбүз.", reply_markup=get_main_keyboard())

@dp.message(F.text.casefold() == "стоп")
async def stop_troll(message: types.Message):
    user_id = message.from_user.id
    if user_id in trolling_users:
        trolling_users.remove(user_id)
        await message.answer("🛑 Автоматтык режим өчүрүлдү. Тыныгуу! 😊", reply_markup=get_main_keyboard())
    else:
        await message.answer("Режим и так өчүк эле.", reply_markup=get_main_keyboard())

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
        await message.answer("Ыр издөө үчүн <b>«трек [аты]»</b> деп жазыңыз же <b>«Старт слова»</b> баскычын басыңыз.", parse_mode="HTML", reply_markup=get_main_keyboard())

async def main():
    asyncio.create_task(background_proactive_messenger())
    print("Бот ийгиликтүү иштеди!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
