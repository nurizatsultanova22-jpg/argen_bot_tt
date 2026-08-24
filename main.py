import asyncio
import random
import os
import re
import time
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = "8981337963:AAEbzzI1j3Xh34ACTb2qd3Do6bC9OKeZVYc"

bot = Bot(token=TOKEN)
dp = Dispatcher()

ADMIN_ID = 7978591176  

user_balances = {}
user_stats = {} 
current_bets = {}  
bonus_limits = {}
give_money_limits = {} 
last_roulette_results = ["10⚫", "5🔴", "2⚫", "10⚫", "2⚫", "11🔴", "5🔴", "12⚫", "0🟢"]

def get_balance(user_id):
    if user_id == ADMIN_ID:
        if ADMIN_ID not in user_balances:
            user_balances[ADMIN_ID] = 999999999999999999
        return user_balances[ADMIN_ID]
        
    if user_id not in user_balances:
        user_balances[user_id] = 5000  
    return user_balances[user_id]

def get_user_stats(user_id):
    if user_id not in user_stats:
        user_stats[user_id] = {"won": 0, "lost": 0, "max_win": 0, "max_bet": 0, "games_played": 0}
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
        types.InlineKeyboardButton(text="Крутить", callback_data="action_spin")
    )
    return builder.as_markup()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    text = "Бот успешно запущен! Делайте ставки на рулетку или играйте в бандит."
    await message.answer(text)

@dp.message(Command("id"))
async def cmd_my_id(message: types.Message):
    user_id = message.from_user.id
    await message.answer(f"🆔 Ваш ID: `{user_id}`", parse_mode="Markdown")

@dp.message(F.text.lower().in_({"б", "баланс"}))
async def cmd_balance_simple(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    bal = get_balance(user_id)
    
    response = f"KNK-{user_name}\nмонеты: {bal} 🌒"
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Бонус ↗", callback_data="claim_bonus"))
    
    await message.answer(response, reply_markup=builder.as_markup())

@dp.message(F.text.lower().in_({"профиль", "📋профиль"}))
async def cmd_profile(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    bal = get_balance(user_id)
    stats = get_user_stats(user_id)
    
    response = (
        f"👤 **Профиль игрока KNK-{user_name}**\n\n"
        f"💳 Баланс: **{bal}** 🌒\n"
        f"🎮 Сыграно игр: {stats['games_played']}\n"
        f"🔥 Всего выиграно: **+{stats['won']}** 🌒\n"
        f"📉 Всего проиграно: **-{stats['lost']}** 🌒\n"
        f"👑 Максимальный выигрыш: **{stats['max_win']}** 🌒\n"
        f"⚡ Максимальная ставка: **{stats['max_bet']}** 🌒"
    )
    await message.answer(response, parse_mode="Markdown")

@dp.message(F.text.lower().in_({"стати", "статистика", "рекорд", "рекорды", "топ"}))
async def cmd_stats_top(message: types.Message):
    if not user_stats:
        await message.answer("📊 Пока нет данных об игроках.")
        return

    sorted_users = sorted(user_stats.items(), key=lambda x: x[1]['won'], reverse=True)[:10]
    
    text = "🏆 **Топ игроков по выигрышам:**\n\n"
    for i, (u_id, st) in enumerate(sorted_users, 1):
        text += f"{i}. ID `{u_id}` — Уткан: **+{st['won']}** 🌒 (Макс: {st['max_win']})\n"
        
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text.lower().in_({"лог", "логи"}))
async def cmd_logs(message: types.Message):
    logs_text = "\n".join(last_roulette_results[-12:])
    await message.answer(logs_text)

@dp.message(F.text.lower().in_({"рулетка", "меню"}))
async def cmd_roulette_menu(message: types.Message):
    text = (
        "Минирулетка\n"
        "Угадайте число от 0 до 12 или цвет!\n"
        "Примеры ставок:\n"
        "• 10000 1 (или 10000 на 1)\n"
        "• 5000 7\n"
        "• 1000 на красное"
    )
    await message.answer(text, reply_markup=get_roulette_keyboard())

@dp.message(F.text.lower().in_({"🛒магазин"}))
async def cmd_shop(message: types.Message):
    shop_text = (
        "🎁 Лицензия на свадьбу - 100к монет\n"
        "🔒 Снятие лимита рулетки в группе - 2кк монет\n"
        "🐵 Невидимка от !бот ищи - 250к монет\n"
        "🚫 Защита от !бот стоп - 1кк монет"
    )
    await message.answer(shop_text)

@dp.message(F.text.lower().in_({"📖помощь", "помощь", "/help"}))
async def cmd_help(message: types.Message):
    help_text = "📖 Справка: пишите 'рулетка', 'профиль', 'стати', 'бандит' или делайте ставки числом (например: `10000 1`)."
    await message.answer(help_text)

@dp.message(F.text.lower().in_({"💳 донат", "донат"}))
async def cmd_donate_text(message: types.Message):
    donate_text = (
        "Монеты🪙\n"
        "200.000 - 100₽\n"
        "500.000 - 230₽\n"
        "1.000.000 - 450₽\n"
        "2.000.000 - 845₽\n"
        "5.000.000 - 2.000₽\n"
        "10.000.000 - 4.000₽\n\n"
        "Если возникнут вопросы, Вы можете обратиться к: @Argen_70"
    )
    await message.answer(donate_text)

@dp.message(F.text.regexp(r"^[\+\+\s]*(\d+)$"))
async def add_money_by_reply_or_mention(message: types.Message):
    match = re.match(r"^[\+\+\s]*(\d+)$", message.text.strip())
    if not match:
        return
        
    amount = int(match.group(1))
    sender_id = message.from_user.id
    sender_name = message.from_user.first_name
    
    target_user_id = None
    target_name = ""

    if message.reply_to_message and message.reply_to_message.from_user:
        target_user_id = message.reply_to_message.from_user.id
        target_name = message.reply_to_message.from_user.first_name
    elif message.entities:
        for entity in message.entities:
            if entity.type == "text_mention":
                target_user_id = entity.user.id
                target_name = entity.user.first_name

    if target_user_id:
        if target_user_id == sender_id:
            await message.answer("❌ Нельзя переводить монеты самому себе!")
            return

        if sender_id != ADMIN_ID:
            current_time = time.time()
            if sender_id in give_money_limits:
                last_time = give_money_limits[sender_id]
                if current_time - last_time < 86400:
                    hours_left = int((86400 - (current_time - last_time)) / 3600)
                    await message.answer(f"❌ Лимит! Вы можете дарить монеты через отметку только 1 раз в 24 часа. Подождите еще {hours_left} ч.")
                    return

            sender_bal = get_balance(sender_id)
            if sender_bal < amount:
                await message.answer(f"❌ У вас недостаточно монет для перевода ({amount}). Баланс: {sender_bal}")
                return
            
            user_balances[sender_id] -= amount
            give_money_limits[sender_id] = current_time

        if target_user_id not in user_balances:
            user_balances[target_user_id] = 5000
        user_balances[target_user_id] += amount
        
        await message.answer(f"✅ Успешно! KNK-{target_name} получил +{amount} 🌒 от KNK-{sender_name}\n💳 Баланс: {user_balances[target_user_id]} 🌒")

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
    stats['games_played'] += 1
    if bet_amount > stats['max_bet']:
        stats['max_bet'] = bet_amount

    dice_msg = await message.answer_dice(emoji="🎰")
    await asyncio.sleep(3.5)
    val = dice_msg.dice.value
    
    # 🎰 Telegram кубик маанилери: 64, 43, 22 - бардык барабар символдор (жжекпот/окшош түшүү)
    # 64 көбүнчө 777 (эң жогорку утуш) болуп саналат
    if val == 64:
        win_amount = 70000  # 777 түшкөндө так 70,000
    elif val in [22, 43]:
        win_amount = random.choice([10000, 20000])  # Окшош тушсо 10к же 20к
    else:
        win_amount = 0

    if win_amount > 0:
        if user_id == ADMIN_ID:
            user_balances[ADMIN_ID] += win_amount
        else:
            if user_id not in user_balances:
                user_balances[user_id] = 5000
            user_balances[user_id] += win_amount

        stats['won'] += win_amount
        if win_amount > stats['max_win']:
            stats['max_win'] = win_amount
        await message.answer(f"🎉 Выигрыш в бандите: +{win_amount} 🌒")
    else:
        stats['lost'] += bet_amount
        await message.answer(f"❌ Проигрыш: -{bet_amount} 🌒")

@dp.message(F.text.regexp(r"^ва-банк\s*([кч]|\d+|на\s*красное|на\s*чёрное|красное|чёрное|к|ч|\d+)$", flags=re.IGNORECASE))
async def parse_vabank(message: types.Message):
    text = message.text.strip().lower()
    target = text.replace("ва-банк", "").strip()
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    bal = get_balance(user_id)
    
    if bal <= 0 and user_id != ADMIN_ID:
        await message.answer(f"KNK-{user_name}, у вас 0 монет, ва-банк невозможен ❌")
        return
        
    amount = bal if user_id != ADMIN_ID else 1000000 
    if target.isdigit():
        color = target
        color_text = f"на {target}"
    elif "к" in target or "красн" in target:
        color = "красное"
        color_text = "на красное"
    elif "ч" in target or "чёрн" in target or "черн" in target:
        color = "чёрное"
        color_text = "на чёрное"
    else:
        await message.answer("Ошибка! Напишите правильно: `ва-банк к` или `ва-банк 7`")
        return
        
    current_bets[user_id] = {"amount": amount, "color": color, "name": user_name}
    stats = get_user_stats(user_id)
    if amount > stats['max_bet']:
        stats['max_bet'] = amount

    if user_id != ADMIN_ID:
        user_balances[user_id] = 0
    
    await message.answer(f"Ставка принята: KNK-{user_name} {amount} монет {color_text}")

# Каалаган сандагы ставкаларды кабыл алуу (мисалы: 10000 1, 5000 7, 3000 на красное)
@dp.message(F.text.regexp(r"^(\d+)\s*(?:на\s*)?([кч]|\d+|красное|чёрное|черное|к|ч)$", flags=re.IGNORECASE))
async def parse_bet(message: types.Message):
    text = message.text.strip()
    match = re.match(r"^(\d+)\s*(?:на\s*)?(.*)$", text, re.IGNORECASE)
    if not match:
        return
        
    amount = int(match.group(1))
    target = match.group(2).lower().strip()
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    bal = get_balance(user_id)
    if bal < amount and user_id != ADMIN_ID:
        await message.answer(f"KNK-{user_name}, недостаточно монет ❌")
        return
        
    if target.isdigit():
        color = target
        color_text = f"на {target}"
    elif "к" in target or "красн" in target:
        color = "красное"
        color_text = "на красное"
    elif "ч" in target or "чёрн" in target or "черн" in target:
        color = "чёрное"
        color_text = "на чёрное"
    else:
        return
        
    current_bets[user_id] = {"amount": amount, "color": color, "name": user_name}
    stats = get_user_stats(user_id)
    if amount > stats['max_bet']:
        stats['max_bet'] = amount

    if user_id != ADMIN_ID:
        user_balances[user_id] -= amount
    
    await message.answer(f"Ставка принята: KNK-{user_name} {amount} монет {color_text}")

@dp.message(F.text.lower().in_({"го", "рулетка крутит", "крутить"}))
async def spin_roulette(message: types.Message):
    if not current_bets:
        await message.answer("⚠️ Ни у кого нет активных ставок! Сначала сделайте ставку (например: `10000 1` же `5000 7`)")
        return
        
    msg = await message.answer(f"🎰 Крутим рулетку... (осталось 7 сек.)")
    for sec in range(6, 0, -1):
        await asyncio.sleep(1.0)
        try:
            await msg.edit_text(f"🎰 Крутим рулетку... (осталось {sec} сек.)")
        except:
            pass

    try:
        await msg.delete()
    except:
        pass

    # Монеталар төгүлгөн анимация (GIF/Видео)
    anim_msg = None
    try:
        anim_msg = await message.answer_animation(
            animation="https://media.giphy.com/media/3o7TKSjRrfIPjeiVyM/giphy.gif", 
            caption="🎲 Монеты летят... Рулетка крутится!"
        )
    except:
        try:
            anim_msg = await message.answer_video(
                video="https://www.learningcontainer.com/wp-content/uploads/2020/05/sample-mp4-file.mp4", 
                caption="🎲 Рулетка крутится..."
            )
        except:
            anim_msg = await message.answer("🎲 [Монеты падают... Рулетка крутится]")

    await asyncio.sleep(3.0)

    try:
        await anim_msg.delete()
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
    response = f"🎰 Рулетка выпала: {winning_result}\n\n"

    active_bets_copy = current_bets.copy()
    current_bets.clear()

    for u_id, bet in active_bets_copy.items():
        u_name = bet["name"]
        stats = get_user_stats(u_id)
        stats['games_played'] += 1
        
        is_win = False
        if str(bet["color"]) == str(winning_number):
            is_win = True
            win_multiplier = 12 if winning_number != 0 else 14
            win_amount = bet["amount"] * win_multiplier
        elif bet["color"] == win_color:
            is_win = True
            win_amount = bet["amount"] * 2
        else:
            win_amount = 0

        if is_win:
            if u_id == ADMIN_ID:
                user_balances[ADMIN_ID] += win_amount
            else:
                if u_id not in user_balances:
                    user_balances[u_id] = 5000
                user_balances[u_id] += win_amount
                
            stats['won'] += win_amount
            if win_amount > stats['max_win']:
                stats['max_win'] = win_amount
            response += f"🎉 KNK-{u_name} выиграл {win_amount} 🌒\n"
        else:
            stats['lost'] += bet["amount"]
            response += f"❌ KNK-{u_name} проиграл {bet['amount']} 🌒\n"
        
        current_bal = get_balance(u_id)
        response += f"💳 Баланс: {current_bal} 🌒\n------------------\n"
    
    await message.answer(response)

@dp.callback_query()
async def callback_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_name = callback.from_user.first_name
    data = callback.data
    
    if data == "claim_bonus":
        current_time = time.time()
        if user_id in bonus_limits:
            last_time = bonus_limits[user_id]
            if current_time - last_time < 86400:
                hours_left = int((86400 - (current_time - last_time)) / 3600)
                mins_left = int(((86400 - (current_time - last_time)) % 3600) / 60)
                await callback.answer(f"❌ Вы уже получили бонус сегодня! Подождите еще {hours_left} ч. {mins_left} мин.", show_alert=True)
                return
                
        bonus_limits[user_id] = current_time
        bonus_amount = 10000
        
        if user_id != ADMIN_ID:
            if user_id not in user_balances:
                user_balances[user_id] = 5000
            user_balances[user_id] += bonus_amount
        else:
            user_balances[ADMIN_ID] += bonus_amount
        
        await callback.answer(f"🎉 Вы успешно получили ежедневный бонус: +{bonus_amount} 🌒!", show_alert=True)
        
        new_bal = get_balance(user_id)
        await callback.message.edit_text(f"KNK-{user_name}\nмонеты: {new_bal} 🌒")
        return

    if data == "bet_red_1k":
        bal = get_balance(user_id)
        if bal < 1000 and user_id != ADMIN_ID:
            await callback.answer("Недостаточно монет!", show_alert=True)
            return
        current_bets[user_id] = {"amount": 1000, "color": "красное", "name": user_name}
        if user_id != ADMIN_ID:
            user_balances[user_id] -= 1000
        await callback.message.answer(f"Ставка принята: KNK-{user_name} 1000 монет на красное")
    elif data == "bet_black_1k":
        bal = get_balance(user_id)
        if bal < 1000 and user_id != ADMIN_ID:
            await callback.answer("Недостаточно монет!", show_alert=True)
            return
        current_bets[user_id] = {"amount": 1000, "color": "чёрное", "name": user_name}
        if user_id != ADMIN_ID:
            user_balances[user_id] -= 1000
        await callback.message.answer(f"Ставка принята: KNK-{user_name} 1000 монет на чёрное")
    elif data == "bet_green_1k":
        bal = get_balance(user_id)
        if bal < 1000 and user_id != ADMIN_ID:
            await callback.answer("Недостаточно монет!", show_alert=True)
            return
        current_bets[user_id] = {"amount": 1000, "color": "зелёный", "name": user_name}
        if user_id != ADMIN_ID:
            user_balances[user_id] -= 1000
        await callback.message.answer(f"Ставка принята: KNK-{user_name} 1000 монет на зелёный")
    elif data == "action_spin":
        fake_msg = callback.message
        fake_msg.from_user = callback.from_user
        await spin_roulette(fake_msg)
    await callback.answer()

async def main():
    print("Bot started successfully!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
