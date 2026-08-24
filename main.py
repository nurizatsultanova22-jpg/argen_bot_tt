import asyncio
import datetime
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command

# Токениңизди бул жерге жазыңыз
TOKEN = "TOKEN_BURAGA_JAZYNIZ"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Убактылуу сактоочу базалар (Бул жерди өзүңүздүн SQLite/PostgreSQL базаңызга алмаштырасыз)
user_balances = {}  # {user_id: balance}
daily_stats = {}    # {user_id: {"date": "YYYY-MM-DD", "won": 0, "lost": 0}}


# 1. "Рекорд" буйругу (Күн бою канча утканын жана утулганын көрсөтүү)
@dp.message(Command("рекорд"))
@dp.message(F.text.lower() == "рекорд")
async def show_record(message: types.Message):
    user_id = message.from_user.id
    today = str(datetime.date.today())
    
    # Колдонуучунун бүгүнкү статистикасын алуу
    user_stat = daily_stats.get(user_id, {"date": today, "won": 0, "lost": 0})
    
    # Эгер башка күн болсо статистиканы жаңылайбыз
    if user_stat["date"] != today:
        user_stat = {"date": today, "won": 0, "lost": 0}
        daily_stats[user_id] = user_stat

    won = user_stat["won"]
    lost = user_stat["lost"]
    
    text = (
        f"📊 **Сиздин бүгүнкү көрсөткүчтөр:**\n\n"
        f"🟢 Утканыңыз: **{won:,}** 💰\n"
        f"🔴 Уттурганыңыз: **{lost:,}** 📉\n\n"
        f"✨ Күнүңүз ийгиликтүү улансын!"
    )
    await message.reply(text, parse_mode="Markdown")


# 2. Балансты кошуу (+10000 же башка сумманы башка бирөөнүн билдирүүсүнө реплай кылып жазуу аркылуу)
@dp.message(F.reply_to_message)
async def add_balance_by_reply(message: types.Message):
    text = message.text.strip() if message.text else ""
    
    # Билдирүү '+' белгиси менен башталганын текшеребиз (мисалы: "+10000")
    if text.startswith("+"):
        try:
            # Плюстен кийинки санды бөлүп алабыз
            amount_str = text.replace("+", "").strip()
            amount = int(amount_str)
            
            target_user = message.reply_to_message.from_user
            target_id = target_user.id
            target_name = target_user.first_name
            
            # Балансты жаңыртуу
            if target_id not in user_balances:
                user_balances[target_id] = 0
            user_balances[target_id] += amount
            
            current_balance = user_balances[target_id]
            
            await message.reply(
                f"✅ Ийгиликтүү!\n"
                f"👤 {target_name} аттуу колдонуучуга **{amount:,}** кошулду. 🎁\n"
                f"💳 Учурдагы балансы: **{current_balance:,}**",
                parse_mode="Markdown"
            )
        except ValueError:
            # Эгер плюстен кийин сан туура эмес жазылса үн катпайбыз
            pass


# Ботту ишке киргизүү
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
