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

# Сиздин ID (Администратор - чексиз монета)
ADMIN_ID = 7978591176  

user_balances = {}
user_stats = {} 
current_bets = {}
last_bets = {}
transfer_limits = {}
last_roulette_results = ["10⚫", "5🔴", "2⚫", "10⚫", "2⚫", "11🔴", "5🔴", "12⚫", "0🟢"]

def get_balance(user_id):
    if user_id == ADMIN_ID:
        return 999999999999999999  
    if user_id not in user_balances:
        user_balances[user_id] = 5000  
    return user_balances[user_id]

def get_user_stats(user_id):
    if user_id not in user_stats:
        user_stats[user_id] = {"won": 0, "lost": 0, "max_win": 0, "max_bet": 0}
    return user_stats[user_id]

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

# --- Скриншоттогудай меню баскычтарын түзүүчү клавиатура («Донат» кошулду) ---
def get_main_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="Главное меню", callback_data="menu_main"),
        types.InlineKeyboardButton(text="Розыгрыши", callback_data="menu_giveaway"),
        types.InlineKeyboardButton(text="Рефералка", callback_data="menu_ref")
    )
    builder.row(
        types.InlineKeyboardButton(text="Буквы", callback_data="menu_letters"),
        types.InlineKeyboardButton(text="Рулетка", callback_data="menu_roulette"),
        types.InlineKeyboardButton(text="Бандит", callback_data="menu_bandit")
    )
    builder.row(
        types.InlineKeyboardButton(text="Блэкджек", callback_data="menu_blackjack"),
        types.InlineKeyboardButton(text="Свадьбы", callback_data="menu_weddings"),
        types.InlineKeyboardButton(text="Статусы", callback_data="menu_status")
    )
    builder.row(
        types.InlineKeyboardButton(text="Админские", callback_data="menu_admin"),
        types.InlineKeyboardButton(text="Прочие", callback_data="menu_other")
    )
    builder.row(
        types.InlineKeyboardButton(text="💳 Донат", callback_data="menu_donate")
    )
    return builder.as_markup()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    text = (
        "Добро пожаловать в @RoyalDnoBot\n"
        "Начав использование бота Вы подтверждаете свое согласие с Пользовательским соглашением\n"
        "Для помощи по командам используйте: /help"
    )
    await message.answer(text, reply_markup=get_main_menu_keyboard())

@dp.message(Command("id"))
async def cmd_my_id(message: types.Message):
    user_id = message.from_user.id
    await message.answer(f"🆔 Ваш ID: `{user_id}`", parse_mode="Markdown")

@dp.message(F.text.lower().in_({"б", "баланс", "профиль", "📋профиль"}))
async def cmd_profile(message: types.Message):
    user_id = message.from_user.id
    bal = get_balance(user_id)
    stats = get_user_stats(user_id)
    
    response = (
        ".♠️❤️\n"
        f"Монеты: {bal}🌕\n"
        f"Выиграно: {stats['won']}\n"
        f"Проиграно: {stats['lost']}\n"
        f"Макс. выигрыш: {stats['max_win']}\n"
        f"Макс. ставка: {stats['max_bet']}"
    )
    await message.answer(response)

@dp.message(F.text.lower().in_({"лог", "логи"}))
async def cmd_logs(message: types.Message):
    logs_text = "\n".join(last_roulette_results[-12:])
    await message.answer(logs_text)

@dp.message(F.text.lower().in_({"рулетка", "меню", "🎮главное меню"}))
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

@dp.message(F.text.lower().in_({"🛒магазин"}))
async def cmd_shop(message: types.Message):
    shop_text = (
        "🎁 Лицензия на свадьбу - 100к монет\n"
        "🔒 Снятие лимита рулетки в группе - 2кк монет\n"
        "🐵 Невидимка от !бот ищи - 250к монет\n"
        "🚫 Защита от !бот стоп - 1кк монет\n"
        "🚫🐵 Защита от !!мут и !бот стоп - 4кк монет"
    )
    await message.answer(shop_text)

@dp.message(F.text.lower().in_({"📖помощь", "помощь", "/help"}))
async def cmd_help(message: types.Message):
    help_text = (
        "📖 Справка по командам\n\n"
        "Выберите раздел:"
    )
    await message.answer(help_text, reply_markup=get_main_menu_keyboard())

# --- ДОНАТ МЕНЮСУ ТЕКСТТИ КОШУУ ---
@dp.message(F.text.lower().in_({"донат", "💳 донат"}))
async def cmd_donate_text(message: types.Message):
    donate_text = (
        "Монеты🪙\n"
        "200.000 - 100₽\n"
        "500.000 - 230₽\n"
        "1.000.000 - 450₽\n"
        "2.000.000 - 845₽\n"
        "5.000.000 - 2.000₽\n"
        "10.000.000 - 4.000₽\n"
        "50.000.000 - 20000₽\n"
        "100.000.000 - 40000₽\n\n"
        "Telegram не сможет помочь с покупками, сделанными через нашего бота,\n"
        "Если возникнут вопросы, Вы можете обратиться к: @Argen_70"
    )
    await message.answer(donate_text)

# --- БАНДИТ (СЛОТ ОЮНУ) СЕКЦИЯСЫ ---
@dp.message(F.text.lower().in_({"бандит", "слот", "однорукий бандит"}))
async def play_bandit(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    bal = get_balance(user_id)
    
    bet_amount = 500
    if bal < bet_amount and user_id != ADMIN_ID:
        await message.answer(f"KNK-{user_name}, недостаточно монет")
        return
        
    if user_id != ADMIN_ID:
        user_balances[user_id] -= bet_amount

    stats = get_user_stats(user_id)
    if bet_amount > stats['max_bet']:
        stats['max_bet'] = bet_amount

    slot_emojis = ["🍇", "🍋", "🍊", "🍒", "7️⃣"]
    res1 = random.choice(slot_emojis)
    res2 = random.choice(slot_emojis)
    res3 = random.choice(slot_emojis)
    
    combination_text = f"{res1} {res2} {res3}"
    
    if res1 == res2 == res3:
        win_amount = bet_amount * 5
        if user_id != ADMIN_ID:
            user_balances[user_id] += win_amount
        stats['won'] += win_amount
        if win_amount > stats['max_win']:
            stats['max_win'] = win_amount
        result_msg = f"{combination_text}\nВыигрыш: {win_amount}🌕"
    else:
        stats['lost'] += bet_amount
        result_msg = f"{combination_text}\nПроигрыш: {bet_amount}🌕"
        
    await message.answer(result_msg)

# --- МОНЕТА КОТОРУУ ЖАНА БЕРҮҮ ---
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
            await message.answer(f"❌ У вас недостаточно монет для перевода ({amount}). Баланс: {sender_bal}")
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
    stats = get_user_stats(user_id)
    if amount > stats['max_bet']:
        stats['max_bet'] = amount

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
    stats = get_user_stats(user_id)
    if amount > stats['max_bet']:
        stats['max_bet'] = amount

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
    stats = get_user_stats(user_id)
    
    if bet["color"] == win_color:
        win_amount = bet["amount"] * 2
        if user_id != ADMIN_ID:
            user_balances[user_id] += win_amount
        stats['won'] += win_amount
        if win_amount > stats['max_win']:
            stats['max_win'] = win_amount
        response += f"🎉 KNK-{user_name} выиграл {win_amount} на {bet['color']}е!"
    else:
        stats['lost'] += bet["amount"]
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
    
    if data == "menu_donate":
        donate_text = (
            "Монеты🪙\n"
            "200.000 - 100₽\n"
            "500.000 - 230₽\n"
            "1.000.000 - 450₽\n"
            "2.000.000 - 845₽\n"
            "5.000.000 - 2.000₽\n"
            "10.000.000 - 4.000₽\n"
            "50.000.000 - 20000₽\n"
            "100.000.000 - 40000₽\n\n"
            "Telegram не сможет помочь с покупками, сделанными через нашего бота,\n"
            "Если возникнут вопросы, Вы можете обратиться к: @Argen_70"
        )
        await callback.message.answer(donate_text)
    elif data == "menu_bandit":
        await callback.message.answer("🎰 Напишите слово **«Бандит»**, чтобы сыграть в слот-автомат!", parse_mode="Markdown")
    elif data == "menu_roulette":
        text = (
            "Минирулетка\n"
            "Угадайте число из:\n"
            "0🟢\n"
            "1🔴 2⚫ 3🔴 4⚫ 5🔴 6⚫\n"
            "7🔴 8⚫ 9🔴 10⚫ 11🔴 12⚫\n"
            "Ставки можно текстом:\n"
            "1000 на красное | 5000 на 12"
        )
        await callback.message.answer(text, reply_markup=get_roulette_keyboard())
    elif data == "menu_main":
        await callback.message.answer("🏠 Вы в главном меню.", reply_markup=get_main_menu_keyboard())
    elif data == "bet_red_1k":
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
        stats = get_user_stats(user_id)
        
        if bet["color"] == win_color:
            win_amount = bet["amount"] * 2
            if user_id != ADMIN_ID:
                user_balances[user_id] += win_amount
            stats['won'] += win_amount
            if win_amount > stats['max_win']:
                stats['max_win'] = win_amount
            response += f"🎉 KNK-{user_name} выиграл {win_amount}!"
        else:
            stats['lost'] += bet["amount"]
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
