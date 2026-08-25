import asyncio
import random
import os
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
last_roulette_results = ["10⚫", "5🔴", "2⚫", "10⚫", "2⚫", "11🔴", "5🔴", "12⚫", "0🟢"]

ROULETTE_GIF_URL = "https://media.giphy.com/media/3oKIPnAiaMCws8nOsE/giphy.gif"

DAILY_REWARDS = [
    5000, 6000, 7000, 8000, 9000, 10000, 50000, 11000, 12000, 17000,
    18000, 19000, 20000, 21000, 22000, 60000, 23000, 24000, 25000
]

user_pass_progress = {}

active_giveaway = {
    "active": False,
    "creator": "LIMONTI",
    "prize": 5000000,
    "min_users": 5,
    "max_users": 150,
    "participants": set()
}

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
        types.InlineKeyboardButton(text="🎁 Ежедневные награды (Pass)", callback_data="daily_pass_menu")
    )
    builder.row(
        types.InlineKeyboardButton(text="🎉 Розыгрыш", callback_data="open_giveaway_menu")
    )
    return builder.as_markup()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    text = (
        "👋 Привет! Добро пожаловать в бота **ZERO**.\n"
        "Баланс показывается только при вводе 'б' или 'баланс'. Меню төмөндө:"
    )
    await message.answer(text, reply_markup=get_roulette_keyboard(), parse_mode="Markdown")

@dp.message(F.text.lower().in_({"б", "баланс"}))
async def cmd_balance_simple(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    bal = get_balance(user_id)
    response = f"{user_name}•🪶\nмонеты: {bal:,} 🌒".replace(",", " ")
    await message.answer(response)

@dp.message(F.text.lower().in_({"профиль", "📋профиль"}))
async def cmd_profile(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    bal = get_balance(user_id)
    stats = get_user_stats(user_id, user_name)
    
    response = (
        f"👤 **Профиль игрока {user_name}**\n\n"
        f"💳 Баланс: **{bal:,}** 🌒\n"
        f"🎮 Сыграно игр: {stats['games_played']}\n"
        f"🔥 Всего выиграно: **+{stats['won']:,}** 🌒\n"
        f"📉 Всего проиграно: **-{stats['lost']:,}** 🌒\n"
        f"🏆 Рекордный выигрыш: **{stats['max_win']:,}** 🌒\n"
        f"📈 Максимальная ставка: **{stats['max_bet']:,}** 🌒"
    ).replace(",", " ")
    await message.answer(response, parse_mode="Markdown")

@dp.message(F.text.lower().in_({"рекорд", "рекорды"}))
async def cmd_records(message: types.Message):
    # Бардык оюнчулардын статистикасын чогултуп, рекорду боюнча сорттойбуз
    all_players = list(user_stats.values())
    if not all_players:
        # Эгер статистика жок болсо, скриншоттогудай дефолт маалымат чыгарабыз
        top1_name, top1_win = "LIMONTI", 28654662
        top2_name, top2_win = "ALIK 1k", 12000000
        top3_name, top3_loss = "KGB°KUBA°03", 20000000
    else:
        # Упайлары боюнча сорттоо
        sorted_by_win = sorted(all_players, key=lambda x: x['max_win'], reverse=True)
        top1_name = sorted_by_win[0]['name'] if len(sorted_by_win) > 0 else "LIMONTI"
        top1_win = sorted_by_win[0]['max_win'] if len(sorted_by_win) > 0 and sorted_by_win[0]['max_win'] > 0 else 28654662

        top2_name = sorted_by_win[1]['name'] if len(sorted_by_win) > 1 else "ALIK 1k"
        top2_win = sorted_by_win[1]['max_win'] if len(sorted_by_win) > 1 and sorted_by_win[1]['max_win'] > 0 else 12000000

        sorted_by_loss = sorted(all_players, key=lambda x: x['lost'], reverse=True)
        top3_name = sorted_by_loss[0]['name'] if len(sorted_by_loss) > 0 else "KGB°KUBA°03"
        top3_loss = sorted_by_loss[0]['lost'] if len(sorted_by_loss) > 0 and sorted_by_loss[0]['lost'] > 0 else 20000000

    record_text = (
        "💰 **Глобальный рекорд дня (топ 3)**\n\n"
        f"🥇 {top1_name} — {top1_win:,} монет\n(рекорд выигрыша)\n"
        f"🥈 {top2_name} — {top2_win:,} монет\n(рекорд выигрыша)\n"
        f"🥉 {top3_name} — {top3_loss:,} монет\n(рекорд проигрыша)\n\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "🎩 **Вор в законе дня**\n"
        "🥇 DEVINE — 2337849 монет\n"
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

@dp.message(F.text.lower().in_({"бандит", "слоты"}))
async def cmd_bandit(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    symbols = ["🍋", "🍒", "🍇", "7️⃣", "💎", "⭐"]
    box_white = "⬜"
    
    msg = await message.answer(
        f"🎰 **Однорукий бандит**\n👤 {user_name}•🪶\n\n"
        f"{box_white} {box_white} {box_white} {box_white} {box_white}"
    )
    
    res1 = random.choice(symbols)
    res2 = random.choice(symbols)
    res3 = random.choice(symbols)
    res4 = random.choice(symbols)
    res5 = random.choice(symbols)
    
    for delay, state in [
        (0.8, f"{res1} {box_white} {box_white} {box_white} {box_white}"),
        (0.8, f"{res1} {res2} {box_white} {box_white} {box_white}"),
        (0.8, f"{res1} {res2} {res3} {box_white} {box_white}"),
        (0.8, f"{res1} {res2} {res3} {res4} {box_white}")
    ]:
        await asyncio.sleep(delay)
        try:
            await msg.edit_text(f"🎰 **Однорукий бандит**\n👤 {user_name}•🪶\n\n{state}")
        except:
            pass
        
    await asyncio.sleep(0.8)
    win_symbols = [res1, res2, res3, res4, res5]
    stats = get_user_stats(user_id, user_name)
    
    if len(set(win_symbols)) == 1:
        win_amt = 50000
        win_msg = f"🎉 ДЖЕКПОТ! Вы выиграли {win_amt:,} 🌒!".replace(",", " ")
        if user_id != ADMIN_ID:
            user_balances[user_id] = get_balance(user_id) + win_amt
        else:
            user_balances[ADMIN_ID] += win_amt
        stats['won'] += win_amt
        if win_amt > stats['max_win']:
            stats['max_win'] = win_amt
    elif len(set(win_symbols)) <= 3:
        win_amt = 10000
        win_msg = f"✨ Отлично! Вы выиграли {win_amt:,} 🌒!".replace(",", " ")
        if user_id != ADMIN_ID:
            user_balances[user_id] = get_balance(user_id) + win_amt
        else:
            user_balances[ADMIN_ID] += win_amt
        stats['won'] += win_amt
        if win_amt > stats['max_win']:
            stats['max_win'] = win_amt
    else:
        win_msg = "❌ К сожалению, вы проиграли."
        stats['lost'] += 1000  # Шаардкы проигрыш эсеби

    # Баланс бандитте чыкпайт, тек гана утуш/жеңилүү кабары чыгат
    try:
        await msg.edit_text(
            f"🎰 **Однорукий бандит**\n👤 {user_name}•🪶\n\n"
            f"{res1} {res2} {res3} {res4} {res5}\n\n"
            f"{win_msg}",
            parse_mode="Markdown"
        )
    except:
        pass

@dp.message(F.text.lower().in_({"розыгрыш", "/розыгрыш"}))
async def cmd_giveaway_start(message: types.Message):
    global active_giveaway
    active_giveaway["active"] = True
    active_giveaway["participants"] = {message.from_user.id}
    
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="💰 Участвовать", callback_data="gw_join"),
        types.InlineKeyboardButton(text="👥 Участники", callback_data="gw_list")
    )
    builder.row(
        types.InlineKeyboardButton(text="🚦 Начать", callback_data="gw_start"),
        types.InlineKeyboardButton(text="❌ Отменить", callback_data="gw_cancel")
    )
    
    text = (
        "🎉 **РОЗЫГРЫШ!** 🎉\n\n"
        f"💎 Создатель: {active_giveaway['creator']}\n"
        f"💰 Призовой фонд: {active_giveaway['prize']:,} монет\n"
        f"👥 Нужно участников: {active_giveaway['min_users']}-{active_giveaway['max_users']}\n"
        f"🏆 Доля: все участники (кто-то больше, кто-то меньше)\n\n"
        f"👥 Участников: {len(active_giveaway['participants'])}\n"
        f"✅ Минимум набран! Можно начинать.\n\n"
        f"⏳ Автостарт через 3 часа"
    ).replace(",", " ")
    
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

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
    
    bal = get_balance(user_id)
    if bal < amount and user_id != ADMIN_ID:
        await message.answer(f"{user_name}•🪶\nНедостаточно монет ❌")
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
        
    # Ставка койгондо баланс чыкпайт, тек гана ставка кабыл алынганы кабарланат
    await message.answer(
        f"✅ **Ставка принята!**\n👤 {user_name}•🪶\n🎯 Сумма: **{amount:,} 🌒** ({color_text})".replace(",", " "), 
        parse_mode="Markdown"
    )

@dp.message(F.text.lower().in_({"го", "рулетка крутит", "крутить"}))
async def spin_roulette(message: types.Message):
    if not current_bets:
        await message.answer("⚠️ Активдүү ставкалар жок!")
        return
        
    gif_msg = await message.answer_animation(
        animation=ROULETTE_GIF_URL,
        caption="🎰 Рулетка крутится..."
    )
    
    for sec in range(3, 0, -1):
        await asyncio.sleep(1)
        try:
            await gif_msg.edit_caption(caption=f"🎰 Рулетка крутится... Осталось: **{sec}** сек.", parse_mode="Markdown")
        except:
            pass
            
    try:
        await gif_msg.delete()
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
    
    response = f"🎯 **Результат рулетки:** {winning_result}\n" \
               f"━━━━━━━━━━━━━━━━━━━\n"

    active_bets_copy = current_bets.copy()
    current_bets.clear()

    for u_id, bets_list in active_bets_copy.items():
        u_name = bets_list[0]["name"]
        stats = get_user_stats(u_id, u_name)
        stats['games_played'] += 1
        
        total_win_for_user = 0
        total_loss_for_user = 0
        
        for bet in bets_list:
            b_amount = bet["amount"]
            b_color = str(bet["color"])
            
            is_win = False
            is_green = (winning_number == 0)
            
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
                if is_green and b_color != "зелёный":
                    half_loss = b_amount // 2
                    refund = b_amount - half_loss
                    total_loss_for_user += half_loss
                    if u_id != ADMIN_ID:
                        user_balances[u_id] += refund 
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
                
            # Рулеткада утқандо да баланс чыкпайт, тек гана утуш суммасы жазылат
            response += f"👤 {u_name}•🪶: 🏆 Выиграл **+{total_win_for_user:,} 🌒**\n".replace(",", " ")
        else:
            stats['lost'] += total_loss_for_user
            response += f"👤 {u_name}•🪶: ❌ Проиграл\n"
    
    await message.answer(response, parse_mode="Markdown")

@dp.callback_query()
async def callback_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_name = callback.from_user.first_name
    data = callback.data
    
    if data == "open_giveaway_menu":
        await cmd_giveaway_start(callback.message)
        await callback.answer()
        return

    elif data == "gw_join":
        active_giveaway["participants"].add(user_id)
        await callback.answer(f"🎉 Вы успешно участвуете в розыгрыше! Всего: {len(active_giveaway['participants'])}", show_alert=True)
        return

    elif data == "gw_list":
        await callback.answer(f"👥 Всего участников в розыгрыше: {len(active_giveaway['participants'])}", show_alert=True)
        return

    elif data == "gw_start":
        if not active_giveaway["participants"]:
            await callback.answer("❌ Участники пока отсутствуют!", show_alert=True)
            return
        winner_id = random.choice(list(active_giveaway["participants"]))
        prize = active_giveaway["prize"]
        
        if winner_id != ADMIN_ID:
            user_balances[winner_id] = get_balance(winner_id) + prize
        else:
            user_balances[ADMIN_ID] += prize
            
        await callback.message.answer(f"🎉 **Розыгрыш завершен!**\n🏆 Победитель получил приз: **{prize:,} 🌒**!".replace(",", " "), parse_mode="Markdown")
        active_giveaway["participants"].clear()
        await callback.answer()
        return

    elif data == "gw_cancel":
        active_giveaway["participants"].clear()
        await callback.message.answer("❌ Розыгрыш отменен.")
        await callback.answer()
        return

    elif data == "open_roulette":
        await cmd_roulette_menu(callback.message)
        await callback.answer()
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
            
        await callback.message.answer(f"✅ **Ставка принята!**\n👤 {user_name}•🪶\n🎯 Сумма: **{amount:,} 🌒** ({c_text})".replace(",", " "), parse_mode="Markdown")
        await callback.answer("Ставка принята!")
        return

    elif data == "action_spin":
        fake_msg = callback.message
        fake_msg.from_user = callback.from_user
        await spin_roulette(fake_msg)
        await callback.answer()
        return

    elif data == "action_repeat":
        if user_id not in last_user_bets:
            await callback.answer("У вас нет предыдущих ставок!", show_alert=True)
            return
        lb = last_user_bets[user_id]
        bal = get_balance(user_id)
        if bal < lb["amount"] and user_id != ADMIN_ID:
            await callback.answer("Недостаточно монет для повторения!", show_alert=True)
            return
        if user_id not in current_bets:
            current_bets[user_id] = []
        current_bets[user_id].append(lb)
        if user_id != ADMIN_ID:
            user_balances[user_id] -= lb["amount"]
        await callback.message.answer(f"✅ **Ставка повторена!**\n👤 {user_name}•🪶\n🎯 Сумма: **{lb['amount']:,} 🌒** ({lb['text']})".replace(",", " "), parse_mode="Markdown")
        await callback.answer("Ставка повторена!")
        return

    elif data == "action_double":
        if user_id not in last_user_bets:
            await callback.answer("У вас нет ставок для удвоения!", show_alert=True)
            return
        lb = last_user_bets[user_id]
        double_amount = lb["amount"] * 2
        bal = get_balance(user_id)
        if bal < double_amount and user_id != ADMIN_ID:
            await callback.answer("Недостаточно монет для удвоения!", show_alert=True)
            return
        new_lb = lb.copy()
        new_lb["amount"] = double_amount
        last_user_bets[user_id] = new_lb
        if user_id not in current_bets:
            current_bets[user_id] = []
        current_bets[user_id].append(new_lb)
        if user_id != ADMIN_ID:
            user_balances[user_id] -= double_amount
        await callback.message.answer(f"✅ **Ставка удвоена!**\n👤 {user_name}•🪶\n🎯 Сумма: **{double_amount:,} 🌒** ({new_lb['text']})".replace(",", " "), parse_mode="Markdown")
        await callback.answer("Ставка удвоена!")
        return

    await callback.answer()

async def main():
    print("Bot started successfully with hidden balances on bets/bandit and custom records!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
