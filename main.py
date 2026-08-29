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

# Өз алдынча (бош убакта) биринчи жазып жиберүүчү сөздөр
proactive_phrases = [
    "Эй шүмшүк, кел зериктинби, азыр энеңди оозго алып сөгүшөбүзбү же сүйлөшөбүзбү? 😈🖕",
    "Ой мал, унчукпай калдың го? Же коркуп калдыҥбы, жериктинби кел сөгүшөлү! 🤬",
    "Эй келесоо, жаман зерикдим, кайсы тешикке кирип кеттиң, кел сүйлөшүп же сөгүшүп алалы! 🗣️",
    "Тынчтыкпы өңүңдө? Же кулагың калпак болуп калдыбы, кел бир аздан сөгүшүп алалы закымдап! 🥊",
    "Эй бетпак, зеригип кеттим окшойт, кел келип кал, сөгүшөлү же сүйлөшөлү! 🥱"
]

# Сөздүн маанисине же жаман/жакшы сөзгө карап жооп берүүчү база
def get_smart_reply(text: str) -> str:
    t = text.lower()
    
    # 1. Жакшы сөздөр, саламдашуулар
    if any(w in t for w in ["салам", "куш", "привет", "жакшы", "кандай", "дос", "брат", "красавчик"]):
        responses = [
            "Оо, брат, өзүң кандай жатасың? Күнүң кандай өтүп жатат? 😎👊",
            "Жакшы шүгүр, өзүңдү карап койчу, чарчабай жүрөсүңбү? Жакшы жашоо! ✨",
            "Салам! Эмне жаңылык, баары жакшыбы же дагы маселе чыктыбы? 🤝",
            "Өзүң жакшы болсоң, мен да сонунмун! Айта бер, эмне кеп? ✌️"
        ]
        return random.choice(responses)
        
    # 2. Ото жаман мат, согунгөн сөздөр келсе (андан өткөрө күчтүү сөгүү)
    if any(w in t for w in ["котогум", "амың", "энең", "ам", "жоон", "сөк", "сойлап", "куудул", "коток", "шалава", "ээн"]):
        bad_responses = [
            "Эй котагымды жебечи, сенин энеңдин амын тешип кетейин, мал неме! 🖕🤬",
            "Энеңди сагындыңбы өңүңдө, сенин котогуңду оозуңа тыгып коем, мал! 👊",
            "Оозуңа карап сүйлө, сенин бүт тукумуңдун амын сыйрып салайын, тескери эшек! 🤮",
            "Котогумду жеп калыптырсың, энеңдин амына тыгып кетейин сени, иттин баласы! 🐕💥",
            "Сен кимди сөгүп жатасың, сенин сойку энеңдин амын ачып салайын, жогол ары! 🖕"
        ]
        return random.choice(bad_responses)

    # 3. Башка учурлар (ар кандай келесоо, шылдың сөздөр)
    general_trolls = [
        "Эй мал, эмне деп күңкүлдөп жатасың түшүнүксүз? Мээң катып калганбы? 🧠🧊",
        "Котогумду жегениң качан калат? Жөн эле отурчу тынч! 💩",
        "Сенин башыңар кичине иштейби же толугу менен токмоктолгонбу? 🤡",
        "Тилиңди тишиңге тиштеп тынч отурбасаң, энеңди оозго алып салайын! 🤬",
        "Ой келесоо, башка акылдуу сөз таппадыңбы? Иттин богуна окшошпо! 🐕"
    ]
    return random.choice(general_trolls)

def get_main_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="Старт слова"))
    builder.row(types.KeyboardButton(text="Стоп"))
    return builder.as_markup(resize_keyboard=True)

# Фондо тынымсыз өз алдынча жазып туруучу функция (Качан зериксе)
async def background_proactive_messenger():
    while True:
        await asyncio.sleep(random.randint(180, 400)) # 3 мүнөттөн 6.5 мүнөткө чейинки убакытта
        for user_id in list(trolling_users):
            try:
                phrase = random.choice(proactive_phrases)
                await bot.send_message(user_id, phrase, reply_markup=get_main_keyboard())
            except Exception:
                pass

@dp.message(F.text.casefold().in_(["/start", "start"]))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    active_users.add(user_id)
    
    await message.answer(
        "👋 <b>Привет!</b> Я музыкальный бот.\n\n"
        "• Чтобы найти песню, напиши: <i>трек [название]</i> или <i>найти [название]</i>\n"
        "• Нажми кнопку <b>«Старт слова»</b>, чтобы включить режим жесткого кыргызского троллинга.\n"
        "• Нажми <b>«Стоп»</b>, чтобы выключить его.",
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
    await message.answer("😈 Режим жесткого кыргызского троллинга активирован! Эми каалаганыңды жаз, сага жараша жооп берем же сөгүшөбүз. Арасында өзүм да жазып турамын!", reply_markup=get_main_keyboard())

@dp.message(F.text.casefold() == "стоп")
async def stop_troll(message: types.Message):
    user_id = message.from_user.id
    if user_id in trolling_users:
        trolling_users.remove(user_id)
        await message.answer("🛑 Режим троллинга выключен. Фух, тыныгуу! 😊", reply_markup=get_main_keyboard())
    else:
        await message.answer("Режим троллинга и так не был включен.", reply_markup=get_main_keyboard())

# --- МУЗЫКА ИЗДӨӨ ЖАНА ОРИГИНАЛДУУ АТ МЕНЕН ЖӨНӨТҮҮ ---
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
        await message.answer("❌ Пожалуйста, укажите название песни после слова «трек» или «найти».", reply_markup=get_main_keyboard())
        return

    wait_msg = await message.answer("🔍 Ищу музыку, подождите...")

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
            await wait_msg.edit_text("❌ Извините, в нашем боте очень много песен, поэтому найти её среди них сложно.", reply_markup=get_main_keyboard())
            return
        
        try:
            await wait_msg.delete()
        except Exception:
            pass

    except Exception as e:
        try:
            await wait_msg.edit_text("❌ Извините, в нашем боте очень много песен, поэтому найти её среди них сложно.", reply_markup=get_main_keyboard())
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
        # Колдонуучунун сөзүн талдап, ошого жараша жакшы же өтө жаман жооп кайтаруу
        reply_text = get_smart_reply(message.text)
        await message.answer(reply_text, reply_markup=get_main_keyboard())
    else:
        await message.answer("Используйте команду <b>«трек [название]»</b> для поиска песни или нажмите кнопку <b>«Старт слова»</b>.", parse_mode="HTML", reply_markup=get_main_keyboard())

async def main():
    # Фондо өз алдынча жазып туруучу тапшырманы кошух
    asyncio.create_task(background_proactive_messenger())
    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
