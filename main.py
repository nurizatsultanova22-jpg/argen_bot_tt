import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import FSInputFile
import aiohttp
import os

# Сиз берген токен туташтырылды
TOKEN = "8620902917:AAHPuthkzK9MT7fGRWe2npjm4mY8ZwRXLWs"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Издөө жана аудио файлды жүктөө функциясы
async def search_and_download_track(query: str):
    search_url = f"https://api.deezer.com/search?q={query}"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(search_url) as response:
            if response.status != 200:
                return None, "Базага туташууда ката кетти."
            
            data = await response.json()
            tracks = data.get("data", [])
            
            if not tracks:
                return None, "Ыр табылган жок. Башка атын жазып көрүңүз."
            
            track = tracks[0]
            track_title = f"{track['artist']['name']} - {track['title']}"
            preview_url = track.get("preview")
            
            if not preview_url:
                return None, "Бул ырдын аудио файлы жеткиликсиз экен."
            
            file_path = "temp_audio.mp3"
            async with session.get(preview_url) as audio_resp:
                if audio_resp.status == 200:
                    with open(file_path, "wb") as f:
                        f.write(await audio_resp.read())
                    return file_path, track_title
                    
    return None, "Ырды жүктөөдө ката кетти."

# 'трек [аты]' деп жазганда иштөөчү бөлүк
@dp.message(F.text.startswith("трек "))
async def send_track(message: types.Message):
    query = message.text[5:].strip()
    
    if not query:
        await message.answer("Сураныч, ырдын атын да кошо жазыңыз. Мисалы: `трек камин`")
        return
        
    waiting_msg = await message.answer("🎵 ыр изделүүдө жана даярдалууда...")
    
    file_path, title_or_error = await search_and_download_track(query)
    
    if file_path:
        audio = FSInputFile(file_path)
        await message.answer_audio(audio=audio, caption=f"🎧 {title_or_error}")
        await waiting_msg.delete()
        
        if os.path.exists(file_path):
            os.remove(file_path)
    else:
        await waiting_msg.edit_text(title_or_error)

async def main():
    print("Бот ишке кирди...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
