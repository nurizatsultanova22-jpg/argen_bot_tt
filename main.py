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

# Кыргызча жаман, жакшы, согунгөн, тийишкен 100дөн ашык сөздөр жана стикерлер/эмодзилер
troll_phrases = [
    "Эй сакалыңды сылай элек мал, оозуңду жаап жүрсөң боло! 🖕😒",
    "Кейпиң куругур, сенин мээңдин ордуна тоң май катып калганбы? 🧠🧊",
    "Койчу ээ, ооздон чыккан сөзүң иттин богына окшойт. 💩🐕",
    "Сени төрөгөн энеге ыدда, эмне деген жоон аяк чочкону чоңойткон! 🐖😂",
    "Тьфу, бетпак неме! Көрүнбөчү көзгө. 🤮",
    "Ой келесоо, сенин башыңа тооктун гана мээси батса керек. 🐔🤪",
    "Жаның чыгып кетсин, баээк! Адам болуп жаралганың калп көрсө. 👻",
    "Андай акмакчылыкты каяктан таап келесиң, тескери баскан эшек? 🫏",
    "Колуңдан эч нерсе келбейт, тим эле мактана бербей жүрү нарктап! 👎",
    "Тилиңди кесип туруп итке ташташ керек сенин! 🐕👅",
    "Оозуңдан чыккан ар бир сөзүң бир челек көң экен. 💩",
    "Келбетиңди кара, күзгүгө өзүң таң каласың го шүмшүк! 🪞👺",
    "Адам катары сүйлөсөң тилиң кычышып кетеби, же көнүп калгансыңбы акмакчылыкка? 🐒",
    "Бар жоголчу ары, мээни жебей! 🛑",
    "Сенин акылсыз башыңды бир таш менен чаап сындыруу керек. 🪨💥",
    "Койчу, сенин сөзүң көк эшектин ырына окшош. 🎶🫏",
    "Сени ким тарбиялаган эле ушундай тескери кежигеси катуу болуп? 🤦‍♂️",
    "Оозуңа абайла, болбосо тишиңди санап берем! 🦷👊",
    "Кантип ушинтип уялбай калп айтасың, бет кап кийген бөрү? 🐺",
    "Жаныңа барууга да жийиркеничтүү, жыттанган неме! 🤢",
    "Сенин аң-сезимиң кирпинин мээсинен да кичине. 🦔",
    "Андай келесоо сөздөрдү башка жакка барып айт, кулагым тынч болсун! 🔇",
    "Арбак ургур, кайдан чыктың мынча жадатып! 👻",
    "Сенин сүйлөгөнүңө ит да күлөт бейм. 🐕😂",
    "Жаныңды жебей, тынч отурсаң болори! 🤫",
    "Келесоолуктун да чеги болот да, эй! 🛑🤡",
    "Кел, сени бир чайкап жибериш керек окшойт, мээң айланып калыптыр. 🌀",
    "Ыйлагың келип турабы же мактанайын дедиңби, байкуш? 🥺",
    "Сенин сөзүң куру жээк, мааниси ноль! 📉",
    "Күн сайын ушинтип башыбызды катырасыңбы, тажатма? 🥱",
    "Ит болсоң да тишиңди көрсөтпөйт элең, сен андан да өткөн экенсиң. 🐕",
    "Түтүнү жок өрт чалабы сени, чарчаттың! 🔥",
    "Кеттиң ошол жакка, шүмшүк! 🚪",
    "Сенин акылсыздыгыңды көргөндө жаканы кармайсың. 🤦‍♀️",
    "Тилиң узун экен, бирок эч нерсеге жарабайт. 📏",
    "Жомогуңду башкага айт, мага өтпөйт! 📖",
    "Караңгы үңкүрдөн чыккандай элең, дагы эле ошол бойдон калыптырсың. 🦇",
    "Адам болбой калган неме экенсиң да. 🚷",
    "Сүйлөсөң акылдуу болуп көрүнөйүн дейсиңби, бирок тескерисинче болууда. 📉",
    "Мээң бош калгандыктан шамал катуу уруп жатат го? 💨",
    "Эсиң барда эсинди жыйып ал, чала молдо! 📚",
    "Өзүңө окшогондорго барып сүйлө, мен чарчадым. 🛌",
    "Ырдасаң да үнүң баканын бакылдаганына окшош. 🐸",
    "Колдон келбеген ишке мурдуңду тыкпа! 👃",
    "Сени бир нерсе кылыш керек, бирок кеч болуп калды окшойт. ⏳",
    "Калпты суудай ичкен адам экенсиң да. 💧🤥",
    "Бетиң калың экен, отко кактаса да күйбөсө керек. 🔥",
    "Жөн эле жүрсөң боло, эмнеге балекетти издейсиң? 🔍",
    "Ой, сенин сөзүңө ит дагы ишенбейт! 🐕",
    "Келесоолуктун профессору болсоң керек, диплом алдынбы? 🎓🤡",
    "Кулагымдын кужурун алдың аягында! 🙉",
    "Тентип кеткен немедей болуп кайдан жүрөсүң? 🚶‍♂️",
    "Кантип ушинтип уялып койбойт адам? 😳",
    "Сенин акылсыз создоруно тунку иттер да улуйт. 🐺🌙",
    "Оозуңду ачсаң эле келесоолук чачырайт. ✨💩",
    "Башың иштебесе тилиңди тыйсаң боло! 🤐",
    "Жалган дүйнөдө сеникидей кызык адам аз эле болсо керек. 🌍",
    "Барган жериңди ылай кылган шумдук экенсиң. 🟤",
    "Сенин сөзүң бир тыйынга да турбайт! 🪙",
    "Чарчаттың го, чарчабаган неме! 😩",
    "Кеттиң оолак, маанайды түшүрбөй! ⚡",
    "Акмактык менен алыска бара албайсың, дос! 🚀",
    "Башыңа мээ эмес, манка толуп калган го? 🤧",
    "Эмне дегениңди өзүң түшүнөсүңбү өңүңдө? 🧐",
    "Шылдың болгонуң аз келгенсип, дагы сүйлөйсүңбү? 🎭",
    "Адам болбой калган айбан экенсиң! 🦍",
    "Жүрөгүң караңгы, сөзүң сасык. 🖤",
    "Өзүңө окшогон акмактарды таап ал да, ошолор менен сүйлөш! 🤝",
    "Жогол көзгө урунбай, кыжырды кайнатпай! 😡",
    "Айткан сөзүңө өзүң ишенет элеңбией? 🤔",
    "Тилиңди тишиңге тиштеп тынч отур! 🦷",
    "Сенин келесоолугуң гезитке жаза турган нерсе! 📰",
    "Кылыктанбай жөн эле жүрсөң болобу? 🙄",
    "Адамдын жинине тийгенден башканы билбейсиңби? ⚡",
    "Жылтырагандын баары алтын эмес, сенин сөзүң баары эле калп! 💎",
    "Берекесиз немесиң да, бир майнап чыкпас сени менен. 🌧️",
    "Келесоо баш мээни кыйнабачы! 🤯",
    "Баарын билгенсип акыл үйрөтпө мага! 🚷",
    "Сенин сөзүң түгөнбөгөн бир тарых экен, курусун! 📜",
    "Жаныңдагыларга да күн көрсөтпөйсүң го? ☀️",
    "Кеттиңрөөнү басып, чарчаттың! 🏃‍♂️",
    "Канткен күндө да адам болбойсуң сен! 🪨",
    "Тил албаган өжөр текеге окшойсуң. 🐐",
    "Мээңди тазалап жууп салыш керек экен. 🧽",
    "Ыйманды каякка таштап келдиң эле? ⛪",
    "Оозуңдан акыл чыкпайт, топурак эле чачырайт. 🌪️",
    "Кандай гана тажаал немесиң! 👹",
    "Текке кетти сага кеткен убактым! ⌛",
    "Акылың түн ортосунда уктап калат окшойт. 🌙",
    "Кеттиң ары, маанайды түшүргөн акмак! 😾"
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
        "• Нажми кнопку <b>«Старт слова»</b>, чтобы включить режим кыргызского троллинга.\n"
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
    await message.answer("😈 Режим кыргызского троллинга активирован! Теперь я буду отвечать на каждое твое слово колоритными фразами со стикерами. Попробуй написать что-нибудь!", reply_markup=get_main_keyboard())

@dp.message(F.text.casefold() == "стоп")
async def stop_troll(message: types.Message):
    user_id = message.from_user.id
    if user_id in trolling_users:
        trolling_users.remove(user_id)
        await message.answer("🛑 Режим троллинга выключен. Фух, отдохнем! 😊", reply_markup=get_main_keyboard())
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
        random_phrase = random.choice(troll_phrases)
        await message.answer(random_phrase, reply_markup=get_main_keyboard())
    else:
        await message.answer("Используйте команду <b>«трек [название]»</b> для поиска песни или нажмите кнопку <b>«Старт слова»</b>.", parse_mode="HTML", reply_markup=get_main_keyboard())

async def main():
    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
