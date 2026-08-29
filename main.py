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
# Троллинг режиминде турган колдонуучулар
trolling_users = set()

# 70+ шылдыңдаган жана тийишкен сөздөр тизмеси
troll_phrases = [
    "Ой, давай умничай дальше, профессор диванный дивана! 🥱",
    "С тобой спорить — как в шахматы с голубем играть: фигуры раскидает, на доску нагадит и доволен.",
    "Ты когда говоришь, такое ощущение, будто в интернете за тебя кто-то другой думает.",
    "Твоя логика сейчас где-то в отпуске, причем бессрочном.",
    "Ого, какое заявление! Сам придумал или в TikTok подсмотрел?",
    "Слушай, помолчи лучше, а то от твоих слов батарея на телефоне садится.",
    "Твои мысли — загадка для науки. Главное — никому не рассказывай.",
    "И это всё, на что твоей фантазии хватило?",
    "Смотрю на твои сообщения и думаю: эволюция на тебе решила отдохнуть.",
    "Ой, всё, не дури мне голову, лучше песню поищи нормально.",
    "Ты серьезно думаешь, что это умная мысль была?",
    "Меньше слов, больше дела. Хотя о чем это я, дел от тебя ноль.",
    "У тебя в голове вообще ветер не гуляет? Там целый сквозняк!",
    "Не пытайся казаться умнее, чем есть — мозг сломаешь.",
    "Ой, иди уроки учи, а не со мной спорь.",
    "Твои сообщения вызывают у меня желание зевнуть.",
    "Ну ты и выдал! Цирк уехал, а ты забыл уйти.",
    "Каждый раз удивляюсь, как в такую пустую голову помещается столько ерунды.",
    "Сними корону, она тебе не жмет, она с тебя падает.",
    "Лучше бы молчал, за умного сошел бы точно.",
    "Ой, всё, твой генератор глупостей опять сломался.",
    "Ты бы хоть раз что-то дельное написал, а не это всё.",
    "Твои аргументы такие же слабые, как твой интернет.",
    "С кем поведешься, от того и наберешься... судя по всему, со стеной общаюсь.",
    "Слушать тебя — это как слушать лекцию от табуретки.",
    "У тебя талант говорить много, но смысл оставлять дома.",
    "Ты когда печатаешь, клавиатура сама от стыда не краснеет?",
    "Ой, не смеши мои тапки, они и так устали.",
    "Шел бы ты отсюда со своими гениальными идеями.",
    "Твои слова для меня — пустой звук и шепот ветра.",
    "Иди лучше водички попей, остынь маленько.",
    "Очередной шедевр мысли... в корзину для мусора.",
    "Тебе бы в театре играть, роль пугала отлично бы подошла.",
    "Сколько смотрю на тебя — столько удивляюсь терпению твоего телефона.",
    "Ну и что это за бред сивой кобылы?",
    "Твой уровень юмора остался где-то в детском саду.",
    "Не напрягай извилину, она у тебя и так в единственном числе.",
    "Ой, гений современности нашелся! Иди уроки делай.",
    "С тобой общаться — всё равно что горохом о стену.",
    "Ты всегда такой зануда или сегодня особый день?",
    "Твои шутки такие плоские, что аж забор позавидует.",
    "Хватит писать ерунду, займись делом уже.",
    "От твоих сообщений у меня процессор плавится от стыда.",
    "Ну и зачем ты это написал? Сам-то понял?",
    "Твои амбиции опережают твой мозг лет на сто.",
    "Устал я от твоих бессмысленных сообщений.",
    "Иди лучше поспи, утро вечера мудренее, а тебе это необходимо.",
    "Ты часом не батарейка «Энерджайзер» по тупости?",
    "Помолчи минуту, дай технике отдохнуть от твоих шедевров.",
    "Ой, всё с тобой понятно, диагноз ясен.",
    "Твои слова весят меньше воздуха.",
    "Не пиши мне больше такое, глаза режет.",
    "Ты что, специально стараешься писать всякую чушь?",
    "Мой антивирус ругается на твои сообщения.",
    "Лучше промолчи, за умного сойдешь стопроцентно.",
    "Твои аргументы разбиваются о реальность, как волны о скалы... только ты пену пускаешь.",
    "У тебя в слове «ум» все буквы перепутались.",
    "Хватит умничать, у тебя это плохо получается.",
    "Смотрю на тебя и думаю: сколько же терпения у вселенной.",
    "Иди уроки учи, эксперт диванный.",
    "Твои мысли блуждают в темноте и не могут найти выход.",
    "Ой, не смеши меня, у меня щеки болят.",
    "Лучше бы книжку почитал, чем мне нервы трепать.",
    "У тебя на всё один ответ, и тот глупый.",
    "Твоя фантазия работает только в направлении глупостей.",
    "С тобой каши не сваришь, только мозги закипят.",
    "Хватит чудить, взрослый же человек (или нет?).",
    "Твои слова — сплошное недоразумение.",
    "Иди выпей чай с ромашкой, успокойся.",
    "Завязывай с этим бредом, серьезно говорю.",
    "Ну всё, твой лимит глупостей на сегодня исчерпан!"
]

def get_main_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="Старт слова"))
    builder.row(types.KeyboardButton(text="Стоп"))
    return builder.as_markup(resize_keyboard=True)

@dp.message(F.text.casefold().in_(["/start", "start"]))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    active_users.add(user_id)
    
    await message.answer(
        "👋 <b>Привет!</b> Я музыкальный бот.\n\n"
        "• Чтобы найти песню, напиши: <i>трек [название]</i> или <i>найти [название]</i>\n"
        "• Нажми кнопку <b>«Старт слова»</b>, чтобы включить режим троллинга.\n"
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

# --- СТАРТ СЛОВА (ТРОЛЛИНГ РЕЖИМИ) ---
@dp.message(F.text.casefold() == "старт слова")
async def start_troll(message: types.Message):
    trolling_users.add(message.from_user.id)
    await message.answer("😈 Режим троллинга активирован! Теперь я буду отвечать на каждое твое слово шпильками. Попробуй написать что-нибудь!", reply_markup=get_main_keyboard())

# --- СТОП РЕЖИМ ---
@dp.message(F.text.casefold() == "стоп")
async def stop_troll(message: types.Message):
    user_id = message.from_user.id
    if user_id in trolling_users:
        trolling_users.remove(user_id)
        await message.answer("🛑 Режим троллинга выключен. Фух, отдохнем! 😊", reply_markup=get_main_keyboard())
    else:
        await message.answer("Режим троллинга и так не был включен.", reply_markup=get_main_keyboard())

# --- «ТРЕК» ЖЕ «НАЙТИ» МЕНЕН ИЗДӨӨ ---
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
        'outtmpl': 'song_%(id)s.%(ext)s',
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
                filename = ydl.prepare_filename(info)
                base, _ = os.path.splitext(filename)
                mp3_path = base + '.mp3'
                return info.get('title', 'Audio'), mp3_path

        loop = asyncio.get_running_loop()
        title, file_path = await loop.run_in_executor(None, download)

        if file_path and os.path.exists(file_path):
            audio_file = types.FSInputFile(file_path)
            await message.answer_audio(
                audio=audio_file, 
                caption=f"🎵 <b>{title}</b>",
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

# --- ТРОЛЛИНГ ИШКЕ АШУУЧУ КАТТАР КАРМООЧУ ---
@dp.message()
async def handle_troll_messages(message: types.Message):
    if not message.text:
        return
    
    user_id = message.from_user.id
    active_users.add(user_id)

    # Эгер колдонуучу троллинг режиминде болсо, тизмеден кокус соз тандап жооп беребиз
    if user_id in trolling_users:
        random_phrase = random.choice(troll_phrases)
        await message.answer(random_phrase, reply_markup=get_main_keyboard())
    else:
        await message.answer("Используйте команду <b>«трек [название]»</b> для поиска песни или нажмите <b>«Старт слова»</b>.", parse_mode="HTML", reply_markup=get_main_keyboard())

async def main():
    print("Бот с функцией троллинга успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
