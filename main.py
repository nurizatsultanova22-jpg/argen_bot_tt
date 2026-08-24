import asyncio
import random
import os
import re
import time
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import MenuButtonWebApp, WebAppInfo

TOKEN = "8981337963:AAEbzzI1j3Xh34ACTb2qd3Do6bC9OKeZVYc"

bot = Bot(token=TOKEN)
dp = Dispatcher()

ADMIN_ID = 7978591176  

user_balances = {}
user_stats = {} 
current_bets = {}  # Колдонуучунун бир нече ставкаларын сактоо үшін списокко өзгөртүлдү: {user_id: [{"amount": ..., "color": ..., "text": ...}]}
bonus_limits = {}
give_money_limits = {} 
game_counter = 0  
last_roulette_results = ["10⚫", "5🔴", "2⚫", "10⚫", "2⚫", "11🔴", "5🔴", "12⚫", "0🟢"]

DAILY_REWARDS = [
    5000, 6000, 7000, 8000, 9000, 10000, 50000, 11000, 12000, 17000,
    18000, 19000, 20000, 21000, 22000, 60000, 23000, 24000, 25000
]

user_pass_progress = {}

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
    builder.row(
        types.InlineKeyboardButton(text="🎁 Ежедневные награды (Pass)", callback_data="daily_pass_menu")
    )
    return builder.as_markup()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    text = (
        "👋 Привет! Добро пожаловать в бота **ZERO**.\n"
        "Нажмите кнопку «Открыть» в профиле или ниже, чтобы забрать ежедневные награды! 🚀"
    )
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🎁 Открыть Pass наград", callback_data="daily_pass_menu"))
    builder.row(types.InlineKeyboardButton(text="🎲 Рулетка", callback_data="open_roulette"))
    
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

async def show_pass_menu(message_or_callback, is_callback=False):
    user_id = message_or_callback.from_user.id
    
    if user_id not in user_pass_progress:
        user_pass_progress[user_id] = {"day": 0, "last_time": 0}
    
    p_data = user_pass_progress[user_id]
    current_day_idx = p_data["day"]
    
    pass_text = (
        "🎁 **ZERO Pass — Ежедневные награды**\n"
        "Заходите в приложение каждый день и забирайте свои монеты по порядку!\n\n"
    )
    
    next_reward = DAILY_REWARDS[current_day_idx] if current_day_idx < len(DAILY_REWARDS) else DAILY_REWARDS[-1]
    
    active_builder = InlineKeyboardBuilder()
    active_builder.row(types.InlineKeyboardButton(text=f"🎁 Забрать награду (День {current_day_idx + 1}: +{next_reward} 🌒)", callback_data=f"claim_pass_{current_day_idx}"))
    active_builder.row(types.InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_main"))
    
    full_text = pass_text + f"Ваш текущий прогресс: **День {current_day_idx + 1}** из {len(DAILY_REWARDS)}"
    
    if is_callback:
        try:
            await message_or_callback.message.edit_text(full_text, reply_markup=active_builder.as_markup(), parse_mode="Markdown")
        except:
            await message_or_callback.message.answer(full_text, reply_markup=active_builder.as_markup(), parse_mode="Markdown")
    else:
        await message_or_callback.answer(full_text, reply_markup=active_builder.as_markup(), parse_mode="Markdown")

@dp.message(F.text.lower().in_({"откырыт", "открыть"}))
async def cmd_open_pass_text(message: types.Message):
    await show_pass_menu(message)

# Скриншоттогудай "б" же "баланс" деп жазганда балансты гана керсетүү
@dp.message(F.text.lower().in_({"б", "баланс"}))
async def cmd_balance_simple(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    bal = get_balance(user_id)
    
    response = f"{user_name}•🪶\nмонеты: {bal} 🌒"
    await message.answer(response)

@dp.message(F.text.lower().in_({"профиль", "📋профиль"}))
async def cmd_profile(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    bal = get_balance(user_id)
    stats = get_user_stats(user_id)
    stats['name'] = user_name
    
    response = (
        f"👤 **Профиль игрока {user_name}**\n\n"
        f"💳 Баланс: **{bal}** 🌒\n"
        f"🎮 Сыграно игр: {stats['games_played']}\n"
        f"🔥 Всего выиграно: **+{stats['won']}** 🌒\n"
        f"📉 Всего проиграно: **-{stats['lost']}** 🌒"
    )
    await message.answer(response, parse_mode="Markdown")

@dp.message(F.text.lower().in_({"стати", "статистика", "рекорд", "рекорды", "топ"}))
async def cmd_stats_top(message: types.Message):
    if not user_stats:
        await message.answer("📊 Пока нет данных об игроках.")
        return

    sorted_by_win = sorted(user_stats.items(), key=lambda x: x[1]['won'], reverse=True)[:3]
    top_win_text = ""
    for i, (u_id, st) in enumerate(sorted_by_win):
        name = st.get('name', f"ID {u_id}")
        top_win_text += f"🥇 **{name}** — {st['won']} монет\n"

    text = f"💰 **Топ игроков**\n{top_win_text}"
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text.lower().in_({"лог", "логи"}))
async def cmd_logs(message: types.Message):
    logs_text = "\n".join(last_roulette_results[-12:])
    await message.answer(logs_text)

@dp.message(F.text.lower().in_({"рулетка", "меню"}))
async def cmd_roulette_menu(message: types.Message):
    text = (
        "Минирулетка ZERO\n"
        "Ставки текстом: `50000 на красное` же `12000 на 0` же `50000 к`"
    )
    await message.answer(text, reply_markup=get_roulette_keyboard())

@dp.message(F.text.lower().in_({"📖помощь", "помощь", "/help"}))
async def cmd_help(message: types.Message):
    await message.answer("📖 Командалар: 'открыть', 'рулетка', 'б' (баланс үчүн), ставкалар.")

@dp.message(F.text.lower().in_({"💳 донат", "донат"}))
async def cmd_donate_text(message: types.Message):
    await message.answer("Монеты ZERO 🪙\nСуроолор боюнча: @Argen_70")

# Ар бир ставканы өзүнчө кабыл алуу жана скриншоттогудай форматта чыгаруу
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
        
    current_bets[user_id].append({"amount": amount, "color": color, "name": user_name})
    
    stats = get_user_stats(user_id)
    stats['name'] = user_name
    if amount > stats['max_bet']:
        stats['max_bet'] = amount

    if user_id != ADMIN_ID:
        user_balances[user_id] -= amount
    
    # Скриншоттогудай ар бир ставка киргенде өзүнчө чыгышы:
    await message.answer(f"{user_name}•🪶\n{amount} {target}")

@dp.message(F.text.lower().in_({"го", "рулетка крутит", "крутить"}))
async def spin_roulette(message: types.Message):
    global game_counter
    if not current_bets:
        await message.answer("⚠️ Активдүү ставкалар жок!")
        return
        
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
    
    response = f"🎰 Рулетка: {winning_result}\n"

    active_bets_copy = current_bets.copy()
    current_bets.clear()

    for u_id, bets_list in active_bets_copy.items():
        u_name = bets_list[0]["name"]
        stats = get_user_stats(u_id)
        stats['name'] = u_name
        stats['games_played'] += 1
        
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
                if u_id == ADMIN_ID:
                    user_balances[ADMIN_ID] += win_amount
                else:
                    if u_id not in user_balances:
                        user_balances[user_id] = 5000
                    user_balances[user_id] += win_amount
                    
                stats['won'] += win_amount
                if win_amount > stats['max_win']:
                    stats['max_win'] = win_amount
                response += f"{u_name}•🪶 выигрывал {win_amount} на {winning_number}\n"
            else:
                if is_green and b_color != "зелёный":
                    half_loss = b_amount // 2
                    refund = b_amount - half_loss
                    stats['lost'] += half_loss
                    if u_id != ADMIN_ID:
                        user_balances[u_id] += refund 
                    response += f"{u_name}•🪶 возврат {refund} монет\n"
                else:
                    stats['lost'] += b_amount
                    response += f"{u_name}•🪶 проиграл {b_amount}\n"
    
    # Жыйынтыкта баланс корсотулбойт (скриншоттогудай талап боюнча)
    await message.answer(response)

@dp.callback_query()
async def callback_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = callback.data
    
    if data == "daily_pass_menu":
        await show_pass_menu(callback, is_callback=True)
        await callback.answer()
        return

    elif data.startswith("claim_pass_"):
        try:
            day_idx = int(data.split("_")[2])
        except:
            return
            
        if user_id not in user_pass_progress:
            user_pass_progress[user_id] = {"day": 0, "last_time": 0}
            
        p_data = user_pass_progress[user_id]
        current_time = time.time()
        
        if p_data["last_time"] > 0 and (current_time - p_data["last_time"] < 86400):
            await callback.answer("❌ Вы уже забирали награду сегодня!", show_alert=True)
            return
            
        if day_idx != p_data["day"]:
            await callback.answer("❌ Эта награда сейчас недоступна!", show_alert=True)
            return
            
        reward_amount = DAILY_REWARDS[day_idx]
        
        if user_id != ADMIN_ID:
            if user_id not in user_balances:
                user_balances[user_id] = 5000
            user_balances[user_id] += reward_amount
        else:
            user_balances[ADMIN_ID] += reward_amount
            
        p_data["day"] = (p_data["day"] + 1) % len(DAILY_REWARDS)
        p_data["last_time"] = current_time
        
        await callback.answer(f"🎉 Сыйлык берилди: +{reward_amount} 🌒", show_alert=True)
        await show_pass_menu(callback, is_callback=True)
        return

    elif data == "back_to_main":
        try:
            await callback.message.edit_text("Меню:", reply_markup=get_roulette_keyboard())
        except:
            await callback.message.answer("Меню:", reply_markup=get_roulette_keyboard())
        await callback.answer()
        return

    elif data == "open_roulette":
        await cmd_roulette_menu(callback.message)
        await callback.answer()
        return

    elif data == "action_spin":
        fake_msg = callback.message
        fake_msg.from_user = callback.from_user
        await spin_roulette(fake_msg)
        
    await callback.answer()

async def main():
    try:
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="Открыть",
                web_app=WebAppInfo(url="https://t.me/RoyalDnoBot")
            )
        )
    except Exception as e:
        print(f"Menu button set error: {e}")

    print("Bot started successfully!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
