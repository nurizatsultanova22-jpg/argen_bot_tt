import asyncio
import random
import os
import re
import time
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = "8620902917:AAHPuthkzK9MT7fGRWe2npjm4mY8ZwRXLWs"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Сиздин ID (Чексиз монета)
ADMIN_ID = 7978591176  

user_balances = {}
current_bets = {}
last_bets = {}
transfer_limits = {}
last_roulette_results = ["10⚫", "5🔴", "2⚫", "10⚫", "2⚫", "11🔴", "5🔴", "12⚫", "0🟢"]

def get_balance(user_id):
    if user_id == ADMIN_ID:
        return 999999999999999999  # Админ үчүн чексиз монета
    if user_id not in user_balances:
        user_balances[user_id] = 5000  # Жаңы киргендерге 5000 монета
    return user_balances[user_id]

def get_roulette_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="1 - 3", callback_data="bet_1_3"),
        types.InlineKeyboardButton(text="4 - 6", callback_data="bet_4_6"),
        types.InlineKeyboardButton(text="7 - 9", callback_data="bet_7_9"),
        types.InlineKeyboardButton(text="10 - 12", callback_data="bet_10_12")
    )
    builder.row(
        types.InlineKeyboardButton(text="1к на 🔴", callback_data="bet_red_1k"),
        types.InlineKeyboardButton(text="1к на ⚫", callback_data="bet_black_1k"),
        types.InlineKeyboardButton(text="1к на 0🟢", callback_data="bet_green_1k")
    )
    builder.row(
        types.InlineKeyboardButton(text="Повторить", callback_data="action_repeat"),
        types.InlineKeyboardButton(text="Удвоить", callback_data="action_double"),
        types.InlineKeyboardButton(text="Крутить", callback_data="action_spin")
    )
    return builder.as_markup()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    bal = get_balance(user_id)
    
    text = (
        f"🤖 Привет, KNK-{user_name}!\n\n"
        "Добро пожаловать в мини-рулетку RDNO 🌕\n"
        "1 крутит монета — делайте ставки и испытывайте удачу!\n\n"
        "📌 **Команды:**\n"
        "• `/id` — узнать свой ID\n"
        "• `б` или `баланс` — проверить баланс\n"
        "• `рулетка` — открыть игровое меню\n"
        "• `лог` — история выпавших чисел\n"
        "• `ID + сумма` (например, `7978591176 + 50000`) — перевести монеты по ID\n\n"
        f"💳 Ваш баланс: {bal} монет"
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("id"))
async def cmd_my_id(message: types.Message):
    user_id = message.from_user.id
    await message.answer(f"🆔 Ваш ID: `{user_id}`", parse_mode="Markdown")

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

@dp.message(F.text.lower().in_({"лог", "логи"}))
async def cmd_logs(message: types.Message):
    logs_text = "\n".join(last_roulette_results[-12:])
    await message.answer(logs_text)

@dp.message(F.text.lower().in_({"рулетка", "меню"}))
async def cmd_roulette_menu(message: types.Message):
    text = (
        "Минирулетка\n"
        "Угадайте число из:\n"
        "0🟢\n"
        "1🔴 2⚫ 3🔴 4⚫ 5🔴 6⚫\n"
        "7🔴 8⚫ 9🔴 10⚫ 11🔴 12⚫\n"
        "Ставки можно текстом:\n"
        "1000 на красное | 5000 на 12"
    )
    await message.answer(text, reply_markup=get_roulette_keyboard())

# Каалаган сумманы ID аркылуу которуу (Мисалы: 7978591176 + 50000)
@dp.message(F.text.regexp(r"^(\d+)\s*\+\s*(\d+)$", flags=re.IGNORECASE))
async def transfer_custom_money(message: types.Message):
    text = message.text.strip()
    match = re.match(r"^(\d+)\s*\+\s*(\d+)$", text, re.IGNORECASE)
    if not match:
        return
        
    target_id = int(match.group(1))
    amount = int(match.group(2))
    sender_id = message.from_user.id
    sender_name = message.from_user.first_name
    
    # Оддинар үчүн лимит текшерилбейт, каалагандай бере алат
    if sender_id != ADMIN_ID:
        current_time = time.time()
        if sender_id in transfer_limits:
            last_time = transfer_limits[sender_id]
            if current_time - last_time < 86400:
                hours_left = int((86400 - (current_time - last_time)) / 3600)
                await message.answer(f"❌ Лимит! Вы можете переводить монеты только 1 раз в 24 часа. Подождите еще примерно {hours_left} ч.")
                return

        sender_bal = get_balance(sender_id)
        if sender_bal < amount:
            await message.answer(f"❌ У вас недостаточно монет для перевода ({amount} монета талап кылынат)! Факт: {sender_bal}")
            return
            
    if target_id == sender_id:
        await message.answer("❌ Нельзя переводить монеты самому себе!")
        return

    if sender_id != ADMIN_ID:
        user_balances[sender_id] -= amount
        transfer_limits[sender_id] = time.time()
        
    if target_id not in user_balances:
        user_balances[target_id] = 5000
    user_balances[target_id] += amount
    
    await message.answer(
        f"✅ Успешный перевод!\n"
        f"✈️ KNK-{sender_name} перевел {amount} монет пользователю с ID: `{target_id}` 🌕\n"
        f"💳 Ваш баланс: {get_balance(sender_id)}",
        parse_mode="Markdown"
    )

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
        
    amount = bal
    
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
    
    await message.answer(f"RDNO\n🔥 ВА-БАНК СТАВКА ПРИНЯТА: ✈️ KNK-{user_name} {amount} {color_text}")

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
        return
        
    current_bets[user_id] = {"amount": amount, "color": color}
    if user_id != ADMIN_ID:
        user_balances[user_id] -= amount
    
    await message.answer(f"RDNO\nСтавка принята: ✈️ KNK-{user_name} {amount} {color_text}")

@dp.message(F.text.lower().in_({"го", "рулетка крутит", "крутить"}))
async def spin_roulette(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    if user_id not in current_bets:
        await message.answer(f"⚠️ KNK-{user_name}, сначала сделайте ставку! Например: `2000 к`")
        return
        
    bet = current_bets[user_id]
    last_bets[user_id] = bet.copy()
    
    gif_url = "https://media.giphy.com/media/3oKIPnAiaMCws8nOsE/giphy.gif"
    sent_msg = None
    try:
        sent_msg = await message.answer_animation(animation=gif_url, caption="⏳ Рулетка крутится...")
    except:
        sent_msg = await message.answer("⏳ Рулетка крутится...")

    await asyncio.sleep(5)
    
    try:
        await sent_msg.delete()
    except:
        pass
    
    winning_number = random.randint(0, 12)
    if winning_number == 0:
        win_color = "зелёный"
        winning_result = f"{winning_number}🟢"
    elif winning_number in [2, 4, 6, 8, 10, 12]:
        win_color = "чёрное"
        winning_result = f"{winning_number}⚫"
    else:
        win_color = "красное"
        winning_result = f"{winning_number}🔴"
        
    last_roulette_results.append(winning_result)
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

@dp.callback_query()
async def callback_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_name = callback.from_user.first_name
    data = callback.data
    
    if data == "bet_red_1k":
        bal = get_balance(user_id)
        if bal < 1000 and user_id != ADMIN_ID:
            await callback.answer("Недостаточно монет!", show_alert=True)
            return
        current_bets[user_id] = {"amount": 1000, "color": "красное"}
        if user_id != ADMIN_ID:
            user_balances[user_id] -= 1000
        await callback.message.answer(f"RDNO\nСтавка принята: ✈️ KNK-{user_name} 1000 на красное")
    elif data == "bet_black_1k":
        bal = get_balance(user_id)
        if bal < 1000 and user_id != ADMIN_ID:
            await callback.answer("Недостаточно монет!", show_alert=True)
            return
        current_bets[user_id] = {"amount": 1000, "color": "чёрное"}
        if user_id != ADMIN_ID:
            user_balances[user_id] -= 1000
        await callback.message.answer(f"RDNO\nСтавка принята: ✈️ KNK-{user_name} 1000 на чёрное")
    elif data == "bet_green_1k":
        bal = get_balance(user_id)
        if bal < 1000 and user_id != ADMIN_ID:
            await callback.answer("Недостаточно монет!", show_alert=True)
            return
        current_bets[user_id] = {"amount": 1000, "color": "зелёный"}
        if user_id != ADMIN_ID:
            user_balances[user_id] -= 1000
        await callback.message.answer(f"RDNO\nСтавка принята: ✈️ KNK-{user_name} 1000 на зелёный")
    elif data == "action_repeat":
        if user_id not in last_bets:
            await callback.answer("Нет предыдущей ставки для повтора!", show_alert=True)
            return
        prev = last_bets[user_id]
        bal = get_balance(user_id)
        if bal < prev["amount"] and user_id != ADMIN_ID:
            await callback.answer("Недостаточно монет для повтора ставки!", show_alert=True)
            return
        current_bets[user_id] = prev.copy()
        if user_id != ADMIN_ID:
            user_balances[user_id] -= prev["amount"]
        await callback.message.answer(f"RDNO\nСтавка повторена: ✈️ KNK-{user_name} {prev['amount']} на {prev['color']}")
    elif data == "action_double":
        if user_id not in current_bets:
            await callback.answer("Сначала сделайте ставку перед удвоением!", show_alert=True)
            return
        curr = current_bets[user_id]
        bal = get_balance(user_id)
        if bal < curr["amount"] and user_id != ADMIN_ID:
            await callback.answer("Недостаточно монет для удвоения!", show_alert=True)
            return
        if user_id != ADMIN_ID:
            user_balances[user_id] -= curr["amount"]
        curr["amount"] *= 2
        await callback.message.answer(f"RDNO\nСтавка удвоена: ✈️ KNK-{user_name} теперь {curr['amount']} на {curr['color']}")
    elif data == "action_spin":
        if user_id not in current_bets:
            await callback.answer("Сначала сделайте ставку!", show_alert=True)
            return
        bet = current_bets[user_id]
        last_bets[user_id] = bet.copy()
        
        gif_url = "https://media.giphy.com/media/3oKIPnAiaMCws8nOsE/giphy.gif"
        sent_msg = None
        try:
            sent_msg = await callback.message.answer_animation(animation=gif_url, caption="⏳ Рулетка крутится...")
        except:
            sent_msg = await callback.message.answer("⏳ Рулетка крутится...")
            
        await asyncio.sleep(5)
        
        try:
            await sent_msg.delete()
        except:
            pass
            
        winning_number = random.randint(0, 12)
        if winning_number == 0:
            win_color = "зелёный"
            winning_result = f"{winning_number}🟢"
        elif winning_number in [2, 4, 6, 8, 10, 12]:
            win_color = "чёрное"
            winning_result = f"{winning_number}⚫"
        else:
            win_color = "красное"
            winning_result = f"{winning_number}🔴"
            
        last_roulette_results.append(winning_result)
        response = f"RDNO\nРулетка: {winning_result}\n"
        if bet["color"] == win_color:
            win_amount = bet["amount"] * 2
            if user_id != ADMIN_ID:
                user_balances[user_id] += win_amount
            response += f"🎉 KNK-{user_name} выиграл {win_amount}!"
        else:
            response += f"❌ KNK-{user_name} проиграл."
        response += f"\n💳 Баланс: {get_balance(user_id)} 🌕"
        del current_bets[user_id]
        await callback.message.answer(response)
    await callback.answer()

async def handle(request):
    return web.Response(text="Bot is running successfully!")

async def main():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Web server started on port {port}")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
