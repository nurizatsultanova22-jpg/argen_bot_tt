import asyncio
import random
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = "8620902917:AAHPuthkzK9MT7fGRWe2npjm4mY8ZwRXLWs"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Баланстар жана ставкалар сакталуучу жай
user_balances = {}
current_bets = {}

def get_balance(user_id):
    if user_id not in user_balances:
        user_balances[user_id] = 124000  # Баштапкы баалуу монета
    return user_balances[user_id]

# 1. Меню же рулетка көрүнүшү
@dp.message(F.text.lower().in_({"рулетка", "/start"}))
async def cmd_roulette(message: types.Message):
    user_id = message.from_user.id
    bal = get_balance(user_id)
    
    text = (
        "Минирулетка\n"
        "Угадайте число из:\n"
        "0🟢\n"
        "1🔴 2⚫ 3🔴 4⚫ 5🔴 6⚫\n"
        "7🔴 8⚫ 9🔴 10⚫ 11🔴 12⚫\n"
        "Ставки можно текстом:\n"
        "1000 на красное | 5000 на 12\n\n"
        f"💳 Балансыңыз: {bal} монета"
    )
    await message.answer(text)

# 2. "б" же "баланс" деп жазганда
@dp.message(F.text.lower().in_({"б", "баланс"}))
async def cmd_balance(message: types.Message):
    user_id = message.from_user.id
    bal = get_balance(user_id)
    await message.answer(f"Монеты: {bal} 🌕")

# 3. Ставкаларды текст менен кабыл алуу (Мисалы: "30000 к" же "5000 ч")
@dp.message(F.text.regexp(r"^(\d+)\s*([кч]|на\s*красное|на\s*чёрное|красное|чёрное|к|ч)$", flags=re.IGNORECASE if 're' in globals() else 0))
async def parse_bet(message: types.Message):
    global re
    import re
    text = message.text.strip()
    match = re.match(r"^(\d+)\s*(.*)$", text, re.IGNORECASE)
    if not match:
        return
        
    amount = int(match.group(1))
    target = match.group(2).lower().strip()
    
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    bal = get_balance(user_id)
    
    if bal < amount:
        await message.answer("❌ Балансыңызда монета жетишсиз!")
        return
        
    if "к" in target or "красн" in target:
        color = "красное"
        color_text = "на красное"
    elif "ч" in target or "чёрн" in target or "черн" in target:
        color = "чёрное"
        color_text = "на чёрное"
    else:
        await message.answer("Сураныч, 'к' (кызыл) же 'ч' (кара) деп жазыңыз. Мисалы: `30000 к`")
        return
        
    current_bets[user_id] = {"amount": amount, "color": color}
    user_balances[user_id] -= amount
    
    log_response = (
        f"RDNO\n"
        f"Ставка принята: ✈️ **{user_name}** {amount} {color_text}"
    )
    await message.answer(log_response, parse_mode="Markdown")

# 4. "Го" же "Крутит" деп жазганда GIF анимация чыгып, андан кийин жыйынтык чыгат
@dp.message(F.text.lower().in_({"го", "рулетка крутит", "крутить"}))
async def spin_roulette(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    if user_id not in current_bets:
        await message.answer("⚠️ Алгач ставка коюңуз! Мисалы: `30000 к`")
        return
        
    bet = current_bets[user_id]
    
    # Видеодогудай маскачан анонимдин рулетка ойноп жаткан GIF анимациясын жөнөтөбүз
    gif_url = "https://media.giphy.com/media/3oKIPnAiaMCws8nOsE/giphy.gif" # Аноним рулетка GIF шилтемеси
    try:
        await message.answer_animation(animation=gif_url, caption="⏳ крутит (через 10 сек)...")
    except:
        await message.answer("⏳ Рулетка айланып жатат...")

    await asyncio.sleep(3) # Имитация үчүн убакыт
    
    winning_number = random.randint(0, 12)
    if winning_number == 0:
        win_color = "зелёный"
        winning_result = "0🟢"
    elif winning_number in [2, 4, 6, 8, 10, 12]:
        win_color = "чёрное"
        winning_result = f"{winning_number}⚫"
    else:
        win_color = "красное"
        winning_result = f"{winning_number}🔴"
        
    response = f"Рулетка: {winning_result}\n"
    
    if bet["color"] == win_color:
        win_amount = bet["amount"] * 2
        user_balances[user_id] += win_amount
        response += f"KNK-{user_name} выиграл {win_amount} на {bet['color']}е 🎉"
    else:
        response += f"KNK-{user_name} проиграл {bet['amount']} на {bet['color']}е ❌"
        
    response += f"\n\n💳 Баланс: {user_balances[user_id]} 🌕"
    
    del current_bets[user_id]
    await message.answer(response)

async def handle(request):
    return web.Response(text="Bot is running!")

async def web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

async def main():
    await web_server()
    print("Рулетка GIF боту ишке кирди...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
