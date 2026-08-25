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

# Розыгрыш үчүн маалыматтар
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

def get_user_stats(user_id):
    if user_id not in user_stats:
        user_stats[user_id] = {"won": 0, "lost": 0, "max_win": 0, "max_bet": 0, "games_played": 0, "name": "Игрок"}
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
        "Балансы и монеты показываются только по запросу ('б' же 'баланс'). Меню төмөндө:"
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
    stats = get_user_stats(user_id)
    
    response = (
        f"👤 **Профиль игрока {user_name}**\n\n"
        f"💳 Баланс: **{bal:,}** 🌒\n"
        f"🎮 Сыграно игр: {stats['games_played']}\n"
        f"🔥 Всего выиграно: **+{stats['won']:,}** 🌒\n"
        f"📉 Всего проиграно: **-{stats['lost']:,}** 🌒"
    ).replace(",", " ")
    await message.answer(response, parse_mode="Markdown")

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

# Ставкаларды текшерүү жана балансты кошо көрсөтүү
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
        await message.answer(f"{user_name}•🪶\nНедостаточно монет ❌\nВаш баланс: {bal:,} 🌒".replace(",", " "))
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
    
    stats = get_user_stats(user_id)
    if amount > stats['max_bet']:
        stats['max_bet'] = amount

    if user_id != ADMIN_ID:
        user_balances[user_id] -= amount
        
    new_bal = get_balance(user_id)
    
    await message.answer(
        f"✅ **Ставка принята!**\n👤 {user_name}•🪶\n🎯 Сумма: **{amount:,} 🌒** ({color_text})\n💳 Баланс: **{new_bal:,} 🌒**".replace(",", " "), 
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
        stats = get_user_stats(u_id)
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
                
            current_bal = get_balance(u_id)
            response += f"👤 {u_name}•🪶: 🏆 Выиграл **+{total_win_for_user:,} 🌒** | Баланс: **{current_bal:,} 🌒**\n".replace(",", " ")
        else:
            stats['lost'] += total_loss_for_user
            current_bal = get_balance(u_id)
            response += f"👤 {u_name}•🪶: ❌ Проиграл | Баланс: **{current_bal:,} 🌒**\n".replace(",", " ")
    
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

    # Калган callback жооптору...
    await callback.answer()

async def main():
    print("Bot started successfully with Giveaway and updated balance logic!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
