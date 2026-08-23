import asyncio
import random
import os
import re
import time
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command

TOKEN = "8620902917:AAHPuthkzK9MT7fGRWe2npjm4mY8ZwRXLWs"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Өзүңүздүн Telegram ID'ңизди 0 ордуна жазыңыз (Админ чексиз монета үчүн)
ADMIN_ID = 0  

user_balances = {}
user_usernames = {}
current_bets = {}
transfer_limits = {}  # {user_id: соңку которгон убакыт}

def get_balance(user_id):
    if user_id == ADMIN_ID:
        return 999999999999999999  # Админ үчүн чексиз монета
    if user_id not in user_balances:
        user_balances[user_id] = 5000  # Жаңы киргендерге 5000 монета
    return user_balances[user_id]

# 1. /start буйругу
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    if message.from_user.username:
        user_usernames[message.from_user.username.lower()] = user_id
        
    bal = get_balance(user_id)
    
    text = (
        f"🤖 Привет, KNK-{user_name}!\n\n"
        "Добро пожаловать в RDNO мини-рулетку.\n"
        "Новым игрокам начислено: 5000 монет 🌕\n\n"
        "📌 **Команды:**\n"
        "• `/id` — узнать свой ID\n"
        "• `б` или `баланс` — проверить баланс\n"
        "• `2000 к` или `1000 ч` — сделать ставку\n"
        "• `ва-банк к` или `ва-банк ч` — сыграть на все монеты!\n"
        "• `@username + 10000` — перевести другу (лимит 1 раз в 24 часа)\n"
        "• `го` — запустить рулетку\n\n"
        f"💳 Ваш баланс: {bal} монета"
    )
    await message.answer(text, parse_mode="Markdown")

# 2. /id буйругу (Ар бир адам өз ID'син билет)
@dp.message(Command("id"))
async def cmd_my_id(message: types.Message):
    user_id = message.from_user.id
    await message.answer(f"🆔 Ваш Telegram ID: `{user_id}`", parse_mode="Markdown")

# 3. Баланс текшерүү ("б" же "баланс")
@dp.message(F.text.lower().in_({"б", "баланс"}))
async def cmd_balance(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    bal = get_balance(user_id)
    
    response = (
        f"RDNO\n"
        f"KNK-{user_name}\n"
        f"Монеты: {bal} 🌕"
    )
    await message.answer(response)

# 4. Досуна отметка кылып 10000 монета которуу (24 сааттык лимит менен)
@dp.message(F.text.regexp(r"^@(\w+)\s*\+\s*10000$", flags=re.IGNORECASE))
async def transfer_money(message: types.Message):
    text = message.text.strip()
    match = re.match(r"^@(\w+)\s*\+\s*10000$", text, re.IGNORECASE)
    if not match:
        return
        
    target_username = match.group(1).lower()
    sender_id = message.from_user.id
    sender_name = message.from_user.first_name
    
    # 24 сааттык лимит текшерүү
    current_time = time.time()
    if sender_id in transfer_limits:
        last_time = transfer_limits[sender_id]
        if current_time - last_time < 86400:  # 24 саат = 86400 секунд
            hours_left = int((86400 - (current_time - last_time)) / 3600)
            await message.answer(f"❌ Лимит! Вы можете переводить бонус только 1 раз в 24 часа. Подождите еще примерно {hours_left} ч.")
            return

    sender_bal = get_balance(sender_id)
    if sender_bal < 10000 and sender_id != ADMIN_ID:
        await message.answer("❌ У вас недостаточно монет для перевода (нужно минимум 10000)!")
        return

    # Алуучуну базадан табуу
    target_id = user_usernames.get(target_username)
    if not target_id:
        await message.answer(f"❌ Пользователь @{target_username} еще не запускал этого бота, перевести невозможно!")
        return
        
    if target_id == sender_id:
        await message.answer("❌ Нельзя переводить монеты самому себе!")
        return

    # Которуу операциясы
    if sender_id != ADMIN_ID:
        user_balances[sender_id] -= 10000
        
    if target_id not in user_balances:
        user_balances[target_id] = 5000
    user_balances[target_id] += 10000
    
    transfer_limits[sender_id] = current_time
    
    await message.answer(
        f"✅ Успешный перевод!\n"
        f"✈️ KNK-{sender_name} перевел 10000 монет пользователю @{target_username} 🌕\n"
        f"💳 Ваш баланс: {get_balance(sender_id)}"
    )

# 5. Ва-банк функциясы ("ва-банк к" же "ва-банк ч")
@dp.message(F.text.regexp(r"^ва-банк\s*([кч]|на\s*красное|на\s*чёрное|красное|чёрное|к|ч)$", flags=re.IGNORECASE))
async def parse_vabank(message: types.Message):
    text = message.text.strip().lower()
    target = text.replace("ва-банк", "").strip()
    
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    bal = get_balance(user_id)
    
    if bal <= 0:
        await message.answer(f"KNK-{user_name}, у вас 0 монет, ва-банк невозможен ❌")
        return
        
    amount = bal  # Бардык баланс
    
    if "к" in target or "красн" in target:
        color = "красное"
        color_text = "на красное (ВА-БАНК)"
    elif "ч" in target or "чёрн" in target or "черн" in target:
        color = "чёрное"
        color_text = "на чёрное (ВА-БАНК)"
    else:
        await message.answer("Ошибка! Напишите правильно: `ва-банк к` или `ва-банк ч`")
        return
        
    current_bets[user_id] = {"amount": amount, "color": color}
    
    if user_id != ADMIN_ID:
        user_balances[user_id] = 0
    
    log_response = (
        f"RDNO\n"
        f"🔥 ВА-БАНК СТАВКА ПРИНЯТА: ✈️ KNK-{user_name} {amount} {color_text}"
    )
    await message.answer(log_response)

# 6. Жөнөкөй ставкаларды кабыл алуу (Мисалы: "2000 к", "1000 ч")
@dp.message(F.text.regexp(r"^(\d+)\s*([кч]|на\s*красное|на\s*чёрное|красное|чёрное|к|ч)$", flags=re.IGNORECASE))
async def parse_bet(message: types.Message):
    text = message.text.strip()
    match = re.match(r"^(\d+)\s*(.*)$", text, re.IGNORECASE)
    if not match:
        return
        
    amount = int(match.group(1))
    target = match.group(2).lower().strip()
    
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    if message.from_user.username:
        user_usernames[message.from_user.username.lower()] = user_id
        
    bal = get_balance(user_id)
    
    if bal < amount:
        await message.answer(f"KNK-{user_name}, недостаточно монет ❌")
        return
        
    if "к" in target or "красн" in target:
        color = "красное"
        color_text = "на красное"
    elif "ч" in target or "чёрн" in target or "черн" in target:
        color = "чёрное"
        color_text = "на чёрное"
    else:
        await message.answer("Используйте: `2000 к` или `1000 ч`")
        return
        
    current_bets[user_id] = {"amount": amount, "color": color}
    
    if user_id != ADMIN_ID:
        user_balances[user_id] -= amount
    
    log_response = (
        f"RDNO\n"
        f"Ставка принята: ✈️ KNK-{user_name} {amount} {color_text}"
    )
    await message.answer(log_response)

# 7. "Го" буйругу (Рулетканы GIF менен айлантуу)
@dp.message(F.text.lower().in_({"го", "рулетка крутит", "крутить"}))
async def spin_roulette(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    if user_id not in current_bets:
        await message.answer(f"⚠️ KNK-{user_name}, сначала сделайте ставку! Например: `2000 к`")
        return
        
    bet = current_bets[user_id]
    
    gif_url = "https://media.giphy.com/media/3oKIPnAiaMCws8nOsE/giphy.gif"
    try:
        await message.answer_animation(animation=gif_url, caption="⏳ крутит (через 5 сек)...")
    except:
        await message.answer("⏳ крутит (через 5 сек)...")

    await asyncio.sleep(4)
    
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
        
    response = f"RDNO\nРулетка: {winning_result}\n"
    
    if bet["color"] == win_color:
        win_amount = bet["amount"] * 2
        if user_id != ADMIN_ID:
            user_balances[user_id] += win_amount
        response += f"🎉 KNK-{user_name} выиграл {win_amount} на {bet['color']}е!"
    else:
        response += f"❌ KNK-{user_name} проиграл {bet['amount']} на {bet['color']}е."
        
    current_bal = get_balance(user_id)
    response += f"\n\n💳 Баланс: {current_bal} 🌕"
    
    del current_bets[user_id]
    await message.answer(response)

# Web server Render үчүн
async def handle(request):
    return web.Response(text="RDNO Bot is running!")

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
    print("Русский RDNO бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
