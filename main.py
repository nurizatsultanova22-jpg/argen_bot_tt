import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import FSInputFile, URLInputFile
import aiohttp
import os

TOKEN = "8620902917:AAHPuthkzK9MT7fGRWe2npjm4mY8ZwRXLWs"

bot = Bot(token=TOKEN)
dp = Dispatcher()

async def search_and_download_track(query: str):
    search_url = f"https://api.deezer.com/search?q={query}"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(search_url) as response:
            if response.status != 200:
                return None, None, None, "Базага туташууда ката кетти."
            
            data = await response.json()
            tracks = data.get("data", [])
            
            if not tracks:
                return None, None, None, "Ыр табылган жок. Башка атын жазып көрүңүз."
            
            track = tracks[0]
            artist_name = track['artist']['name']
            track_title = track['title']
            full_title = f"{artist_name} - {track_title}"
            
            # Альбомдун сүрөтү (обложкасы)
            cover_url = track['album'].get('cover_medium') or track['album'].get('cover_big')
            
            # Превью шилтемеси (Deezer API аркылуу туруктуу келген аудио агым)
            audio_url = track.get("preview")
            
            if not audio_url:
                return None, None, None, "Бул ырдын аудио файлы жеткиликсиз экен."
            
            file_path = "temp_audio.mp3"
            async with session.get(audio_url) as audio_resp:
                if audio_resp.status == 200:
                    with open(file_path, "wb") as f:
                        f.write(await audio_resp.read())
                    return file_path, full_title, cover_url, None
                    
    return None, None, None, "Ырды жүктөөдө ката кетти."

@dp.message(F.text.regexp(r"^(трек|\/трек)\s+(.+)"))
async def send_track(message: types.Message):
    text = message.text.strip()
    if text.startswith("/трек"):
        query = text[5:].strip()
    else:
        query = text[4:].strip()
    
    if not query:
        await message.answer("Сураныч, ырдын атын да кошо жазыңыз. Мисалы: `трек камин`")
        return
        
    waiting_msg = await message.answer("🎵 Ыр изделүүдө жана даярдалууда...")
    
    file_path, title, cover_url, error = await search_and_download_track(query)
    
    if file_path:
        audio = FSInputFile(file_path)
        
        # Эгер альбомдун сүрөтү бар болсо, сүрөтү жана толук аталышы менен жөнөтөбүз
        if cover_url:
            thumbnail = URLInputFile(cover_url)
            await message.answer_audio(
                audio=audio, 
                thumbnail=thumbnail,
                caption=f"🎧 {title}"
            )
        else:
            await message.answer_audio(audio=audio, caption=f"🎧 {title}")
            
        await waiting_msg.delete()
        
        if os.path.exists(file_path):
            os.remove(file_path)
    else:
        await waiting_msg.edit_text(error)

async def main():
    print("Бот ишке кирди...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
