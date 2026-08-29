import asyncio
import logging
import os
import re
from aiogram import Bot, Dispatcher, F, types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from yt_dlp import YoutubeDL

TOKEN = "8797849312:AAEMEvV-WydOdGwElCEzIH44MHpDhvYGmgw"
ADMIN_ID = 7978591176  # Сиздин ID

bot = Bot(token=TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

active_users = set()

@dp.message(F.text.casefold().in_(["/start", "start"]))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    active_users.add(user_id)
    
    await message.answer(
        "👋 <b>Привет!</b> Чтобы найти песню, напиши перед названием слово <b>«трек»</b> или <b>«найти»</b>\n"
        "(Пример: <i>трек eminem</i> или <i>найти без меня</i>)",
        parse_mode="HTML"
    )

# --- АДМИН РАССЫЛКА И БАСКЫЧ КОШУУ ---
@dp.message(F.from_user.id == ADMIN_ID)
async def admin_broadcast_media(message: types.Message):
    if not active_users:
        await message.answer("❌ В базе пока нет пользователей.")
        return

    text_content = message.text or message.caption or ""
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
            if message.text:
                await bot.send_message(
                    chat_id=user_id,
                    text=message.text,
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
        await message.answer("❌ Пожалуйста, укажите название песни после слова «трек» или «найти».")
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
                parse_mode="HTML"
            )
        else:
            await wait_msg.edit_text("❌ Извините, в нашем боте очень много песен, поэтому найти её среди них сложно.")
            return
        
        try:
            await wait_msg.delete()
        except Exception:
            pass

    except Exception as e:
        try:
            await wait_msg.edit_text("❌ Извините, в нашем боте очень много песен, поэтому найти её среди них сложно.")
        except Exception:
            pass
    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

async def main():
    print("Музыкальный бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
