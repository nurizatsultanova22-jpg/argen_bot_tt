import asyncio
import random
import re
import time
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = "8981337963:AAG0tCPAwXo1ldR20VMLODwKPKnsBqgdi4Q"

bot = Bot(token=TOKEN)
dp = Dispatcher()

ADMIN_ID = 7978591176  

user_balances = {}
user_stats = {} 
current_bets = {}  
last_user_bets = {} 
user_history = {} 
last_roulette_results = ["10⚫", "5🔴", "2⚫", "10⚫", "2⚫", "11🔴", "5🔴", "12⚫", "0🟢"]

# Хакер стилиндеги GIF анимациясы
HACKER_GIF_URL = "https://media.giphy.com/media/3oKIPnAiaMCws8nOsE/giphy.gif"

def get_balance(user_id):
    if user_id == ADMIN_ID:
        if ADMIN_ID not in user_balances:
            user_balances[ADMIN_ID] = 999999999999999999
        return user_balances[ADMIN_ID]
        
    if user_id not in user_balances:
        user_balances[user_id] = 5000  
    return user_balances[user_id]

def get_user_stats(user_id, name="Игрок"):
    if user_id not in user_stats:
        user_stats[user_id] = {"won": 0, "lost": 0, "max_win": 0, "max_bet": 0, "games_played": 0, "name": name}
    else:
        user_stats[user_id]["name"] = name
    return user_stats[user_id]

def add_history(user_id, text):
    if user_id not in user_history:
        user_history[user_id] = []
    current_time = time.strftime("[%H:%M:%S]")
    user_history[user_id].insert(0, f"{current_time} 🎰 {text}")
    if len(user_history[user_id]) > 15:
        user_history[user_id].pop()

def get_roulette_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="1 - 3", callback_data="bet_range_1_3"),
        types.InlineKeyboardButton(text="4 - 6", callback_data="bet_range_4_6"),
        types.InlineKeyboardButton(text="7 - 9", callback_data="bet_range_7_9"),
        types.InlineKeyboardButton(text="10 - 12", callback_data="bet_range_10_12")
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
    builder.row(
        types.InlineKeyboardButton(text="🎁 Ежедневный бонус", callback_data="daily_bonus")
    )
    return builder.as_markup()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    args = message.text.split()
    user_id = message.from_user.id
    
    if len(args) > 1 and args[1].isdigit():
        referrer_id = int(args[1])
        if referrer_id != user_id and referrer_id in user_balances:
            user_balances[referrer_id] += 100000
            try:
                await bot.send_message(referrer_id, "🎉 По вашей ссылке зарегистрировался друг! Вам начислено **100 000** монет 🌒!", parse_mode="Markdown")
            except:
                pass

    bot_info = await bot.get_me()
    text = (
        f"🤖 Добро пожаловать в бот **{bot_info.first_name}**!\n\n"
        "Минирулетка\n"
        "Угадайте число из:\n"
        "0🟢\n"
        "1🔴 2⚫ 3🔴 4⚫ 5🔴 6⚫\n"
        "7🔴 8⚫ 9🔴 10⚫ 11🔴 12⚫\n"
        "Ставки можно текстом:\n"
        "1000 на красное | 5000 на 12"
    )
    await message.answer(text, reply_markup=get_roulette_keyboard())

@dp.message(F.text.lower().in_({"б", "баланс"}))
async def cmd_balance_simple(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    bal = get_balance(user_id)
    
    status_title = " 👑 Основатель" if user_id == ADMIN_ID else ""
    bot_info = await bot.get_me()
    
    response = (
        f"🤖 **{bot_info.first_name}**\n"
        f"👤 {user_name}{status_title}\n"
        f"монеты: {bal:,} 🌒"
    ).replace(",", " ")
    await message.answer(response, parse_mode="Markdown")

@dp.message(F.text.lower().in_({"история", "история операций"}))
async def cmd_history(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    status_title = " 👑 Основатель" if user_id == ADMIN_ID else ""
    
    history_list = user_history.get(user_id, ["История пуста"])
    history_str = "\n".join(history_list[:10])
    
    response = (
        f"👤 {user_name}{status_title}\n"
        f"📊 *История операций*\n\n"
        f"{history_str}"
    )
    await message.answer(response, parse_mode="Markdown")

@dp.message(F.text.lower().in_({"рекорд", "рекорды"}))
async def cmd_records(message: types.Message):
    all_players = list(user_stats.values())
    
    if not all_players:
        record_text = (
        "💰 **Глобальный рекорд дня (топ 3)**\n\n"
        "🥇 Игры пока не проводились — 0 монет\n(рекорд выигрыша)\n"
        "🥈 Игры пока не проводились — 0 монет\n(рекорд выигрыша)\n"
        "🥉 Игры пока не проводились — 0 монет\n(рекорд проигрыша)\n\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "🎩 **Вор в законе дня**\n"
        "🥇 Нет данных — 0 монет\n"
        "_Сброс: каждый день в 00:00 (Москва)_\n\n"
        "🎁 **Призы на сегодня**\n"
        "🥇 Выигрыш: 10000000\n"
        "🥈 Проигрыш: 5000000\n"
        "🥉 Вор дня: 15000000\n"
        "_Выплата в 00:00 (Москва)_"
    )
    else:
        # Автоматикалык түрдө реальный оюнчулардан тандап алат
        sorted_by_win = sorted(all_players, key=lambda x: x['max_win'], reverse=True)
        sorted_by_loss = sorted(all_players, key=lambda x: x['lost'], reverse=True)
        
        top1_name = sorted_by_win[0]['name'] if len(sorted_by_win) > 0 and sorted_by_win[0]['max_win'] > 0 else "Игрок 1"
        top1_win = sorted_by_win[0]['max_win'] if len(sorted_by_win) > 0 else 0

        top2_name = sorted_by_win[1]['name'] if len(sorted_by_win) > 1 and sorted_by_win[1]['max_win'] > 0 else "Игрок 2"
        top2_win = sorted_by_win[1]['max_win'] if len(sorted_by_win) > 1 else 0

        top3_name = sorted_by_loss[0]['name'] if len(sorted_by_loss) > 0 and sorted_by_loss[0]['lost'] > 0 else "Игрок 3"
        top3_loss = sorted_by_loss[0]['lost'] if len(sorted_by_loss) > 0 else 0

        record_text = (
            "💰 **Глобальный рекорд дня (топ 3)**\n\n"
            f"🥇 {top1_name} — {top1_win:,} монет\n(рекорд выигрыша)\n"
            f"🥈 {top2_name} — {top2_win:,} монет\n(рекорд выигрыша)\n"
            f"🥉 {top3_name} — {top3_loss:,} монет\n(рекорд проигрыша)\n\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "🎩 **Вор в законе дня**\n"
            f"🥇 {top1_name} — {top1_win:,} монет\n"
            "_Сброс: каждый день в 00:00 (Москва)_\n\n"
            "🎁 **Призы на сегодня**\n"
            "🥇 Выигрыш: 10000000\n"
            "🥈 Проигрыш: 5000000\n"
            "🥉 Вор дня: 15000000\n"
            "_Выплата в 00:00 (Москва)_"
        ).replace(",", " ")
    
    await message.answer(record_text, parse_mode="Markdown")

@dp.message(F.text.lower().in_({"лог", "логи"}))
async def cmd_logs(message: types.Message):
    logs_text = "Последние результаты рулетки:\n" + "\n".join(last_roulette_results[-12:])
    await message.answer(logs_text)

@dp.message(F.text.lower().in_({"бандит", "слоты"}))
async def cmd_bandit(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    status_title = " 👑 Основатель" if user_id == ADMIN_ID else ""
    
    symbols = ["🍋", "🍒", "🍇", "7️⃣", "💎", "⭐"]
    box_white = "⬜"
    
    msg = await message.answer(
        f"🎰 **Однорукий бандит**\n👤 {user_name}{status_title}\n\n"
        f"{box_white} {box_white} {box_white} {box_white} {box_white}"
    )
    
    res1 = random.choice(symbols)
    res2 = random.choice(symbols)
    res3 = random.choice(symbols)
    res4 = random.choice(symbols)
    res5 = random.choice(symbols)
    
    for state in [
        f"{res1} {box_white} {box_white} {box_white} {box_white}",
        f"{res1} {res2} {box_white} {box_white} {box_white}",
        f"{res1} {res2} {res3} {box_white} {box_white}",
        f"{res1} {res2} {res3} {res4} {box_white}"
    ]:
        await asyncio.sleep(0.5)
        try:
            await msg.edit_text(f"🎰 **Однорукий бандит**\n👤 {user_name}{status_title}\n\n{state}")
        except:
            pass
        
    await asyncio.sleep(0.5)
    win_symbols = [res1, res2, res3, res4, res5]
    stats = get_user_stats(user_id, user_name)
    
    bet_amount = 50000 
    
    if len(set(win_symbols)) == 1:
        win_amt = 250000
        win_msg = f"🎉 ДЖЕКПОТ! Вы выиграли {win_amt:,} 🌒!".replace(",", " ")
        if user_id != ADMIN_ID:
            user_balances[user_id] = get_balance(user_id) + win_amt
        else:
            user_balances[ADMIN_ID] += win_amt
        stats['won'] += win_amt
        if win_amt > stats['max_win']:
            stats['max_win'] = win_amt
        add_history(user_id, f"Ставка (слот/бандит): -{bet_amount}")
        add_history(user_id, f"Выигрыш (слот/бандит): +{win_amt}")
    elif len(set(win_symbols)) <= 3:
        win_amt = 100000
        win_msg = f"✨ Отлично! Вы выиграли {win_amt:,} 🌒!".replace(",", " ")
        if user_id != ADMIN_ID:
            user_balances[user_id] = get_balance(user_id) + win_amt
        else:
            user_balances[ADMIN_ID] += win_amt
        stats['won'] += win_amt
        if win_amt > stats['max_win']:
            stats['max_win'] = win_amt
        add_history(user_id, f"Ставка (слот/бандит): -{bet_amount}")
        add_history(user_id, f"Выигрыш (слот/бандит): +{win_amt}")
    else:
        win_msg = "❌ К сожалению, вы проиграли."
        stats['lost'] += bet_amount
        add_history(user_id, f"Ставка (слот/бандит): -{bet_amount}")
        add_history(user_id, f"Проигрыш (слот/бандит): -{bet_amount}")

    try:
        await msg.edit_text(
            f"🎰 **Однорукий бандит**\n👤 {user_name}{status_title}\n\n"
            f"{res1} {res2} {res3} {res4} {res5}\n\n"
            f"{win_msg}",
            parse_mode="Markdown"
        )
    except:
        pass

@dp.message(F.text.regexp(r"^(\d+)\s*(?:на\s*)?([кчз]|\d+|красное|чёрное|черное|зеленый|зелёный|к|ч|з)$", flags=re.IGNORECASE))
async def parse_bet(message: types.Message):
    text = message.text.strip()
    match = re.match(r"^(\d+)\s*(?:на\s*)?(.*)$", text, re.IGNORECASE)
    if not match:
        return
        
    amount = int(match.group(1))
    target = match.group(2).lower().strip()
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    status_title = " 👑 Основатель" if user_id == ADMIN_ID else ""
    
    bal = get_balance(user_id)
    if bal < amount and user_id != ADMIN_ID:
        await message.answer(f"{user_name}{status_title}, ставка не может превышать ваши средства ❌")
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
    elif "з" in target or "зелен" in target:
        color = "зелёный"
        color_text = "на 0"
    else:
        return
        
    if user_id not in current_bets:
        current_bets[user_id] = []
        
    current_bets[user_id].append({"amount": amount, "color": color, "text": color_text, "name": user_name})
    last_user_bets[user_id] = {"amount": amount, "color": color, "text": color_text, "name": user_name}
    
    stats = get_user_stats(user_id, user_name)
    if amount > stats['max_bet']:
        stats['max_bet'] = amount

    if user_id != ADMIN_ID:
        user_balances[user_id] -= amount
        
    add_history(user_id, f"Ставка рулетки: -{amount}")

    await message.answer(
        f"✅ **Ставка принята!**\n👤 {user_name}{status_title}\n🎯 Сумма: **{amount:,} 🌒** ({color_text})".replace(",", " "), 
        parse_mode="Markdown"
    )

@dp.message(F.text.lower().in_({"го", "рулетка крутит", "крутить", "рулетка"}))
async def spin_roulette(message: types.Message):
    if not current_bets:
        await message.answer("⚠️ Активные ставки отсутствуют!")
        return
        
    # 1. Алгач 3 секунд санап таймер көрсөтүү
    timer_msg = await message.answer("🎰 Рулетка запускается через **3** сек...")
    for sec in range(2, 0, -1):
        await asyncio.sleep(1)
        try:
            await timer_msg.edit_text(f"🎰 Рулетка запускается через **{sec}** сек...")
        except:
            pass
            
    try:
        await timer_msg.delete()
    except:
        pass

    # 2. Таймер өчүп, Хакер стилиндеги GIF чыгат
    gif_msg = await message.answer_animation(
        animation=HACKER_GIF_URL,
        caption="🔄 Вращение рулетки..."
    )
    
    await asyncio.sleep(3) # GIF айланып туруу убактысы
    
    try:
        await gif_msg.delete()
    except:
        pass

    # 3. GIF өчкөндөн кийин жыйынтыкты көрсөтүү
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
    
    response = f"🎯 **Результат рулетки:** {winning_result}\n" \
               f"━━━━━━━━━━━━━━━━━━━\n"

    active_bets_copy = current_bets.copy()
    current_bets.clear()

    for u_id, bets_list in active_bets_copy.items():
        u_name = bets_list[0]["name"]
        status_title = " 👑 Основатель" if u_id == ADMIN_ID else ""
        stats = get_user_stats(u_id, u_name)
        stats['games_played'] += 1
        
        total_win_for_user = 0
        total_loss_for_user = 0
        
        for bet in bets_list:
            b_amount = bet["amount"]
            b_color = str(bet["color"])
            
            is_win = False
            if b_color == str(winning_number) or (b_color == "зелёный" and winning_number == 0):
                is_win = True
                win_multiplier = 14 if winning_number == 0 else 12
                win_amount = b_amount * win_multiplier
            elif b_color == win_color:
                is_win = True
                win_amount = b_amount * 2
            else:
                win_amount = 0

            if is_win:
                total_win_for_user += win_amount
            else:
                total_loss_for_user += b_amount

        if total_win_for_user > 0:
            if u_id == ADMIN_ID:
                user_balances[ADMIN_ID] += total_win_for_user
            else:
                if u_id not in user_balances:
                    user_balances[u_id] = 5000
                user_balances[u_id] += total_win_for_user
                
            stats['won'] += total_win_for_user
            if total_win_for_user > stats['max_win']:
                stats['max_win'] = total_win_for_user
                
            add_history(u_id, f"Выигрыш рулетки: +{total_win_for_user}")
            response += f"👤 {u_name}{status_title}: 🏆 Выиграл **+{total_win_for_user:,} 🌒**\n".replace(",", " ")
        else:
            stats['lost'] += total_loss_for_user
            add_history(u_id, f"Проигрыш рулетки: -{total_loss_for_user}")
            response += f"👤 {u_name}{status_title}: ❌ Проиграл\n"
    
    await message.answer(response, parse_mode="Markdown")

@dp.callback_query()
async def callback_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_name = callback.from_user.first_name
    status_title = " 👑 Основатель" if user_id == ADMIN_ID else ""
    data = callback.data
    
    if data == "daily_bonus":
        user_balances[user_id] = get_balance(user_id) + 100000
        await callback.answer("🎁 Вы получили ежедневный бонус 100 000 монет!", show_alert=True)
        return

    elif data.startswith("bet_red_1k") or data.startswith("bet_black_1k") or data.startswith("bet_green_1k"):
        amount = 1000
        bal = get_balance(user_id)
        if bal < amount and user_id != ADMIN_ID:
            await callback.answer("Недостаточно монет ❌", show_alert=True)
            return
            
        if "red" in data:
            color = "красное"
            c_text = "на красное"
        elif "black" in data:
            color = "чёрное"
            c_text = "на чёрное"
        else:
            color = "зелёный"
            c_text = "на 0"
            
        if user_id not in current_bets:
            current_bets[user_id] = []
        current_bets[user_id].append({"amount": amount, "color": color, "text": c_text, "name": user_name})
        last_user_bets[user_id] = {"amount": amount, "color": color, "text": c_text, "name": user_name}
        
        if user_id != ADMIN_ID:
            user_balances[user_id] -= amount
            
        add_history(user_id, f"Ставка рулетки: -{amount}")
        await callback.message.answer(f"✅ **Ставка принята!**\n👤 {user_name}{status_title}\n🎯 Сумма: **{amount:,} 🌒** ({c_text})".replace(",", " "), parse_mode="Markdown")
        await callback.answer("Ставка принята!")
        return

    elif data == "action_spin":
        fake_msg = callback.message
        fake_msg.from_user = callback.from_user
        await spin_roulette(fake_msg)
        await callback.answer()
        return

    await callback.answer()

async def main():
    print("Bot started with timer, hacker gif, auto-records and no default names!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
