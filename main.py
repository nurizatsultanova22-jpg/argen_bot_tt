import asyncio
import logging
import random
import re
from datetime import datetime
from aiogram import Bot, Dispatcher, F, types
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = "8981337963:AAG0tCPAwXo1ldR20VMLODwKPKnsBqgdi4Q"

bot = Bot(token=TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

ADMIN_IDS = {123456789}  # <-- Өзүңүздүн ID'ңизди жазыңыз

users_data = {}
all_wins_records = []   
all_loses_records = []  
daily_transfer_limits = {}

RED_NUMBERS = {1, 3, 5, 7, 9, 11}
BLACK_NUMBERS = {2, 4, 6, 8, 10, 12}

def get_number_emoji(num):
    if num == 0:
        return "💚"
    elif num in RED_NUMBERS:
        return "🔴"
    else:
        return "⚫"

def get_roulette_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="1 - 3", callback_data="bet_range_1_3"),
        types.InlineKeyboardButton(text="4 - 6", callback_data="bet_range_4_6"),
        types.InlineKeyboardButton(text="7 - 9", callback_data="bet_range_7_9"),
        types.InlineKeyboardButton(text="10 - 12", callback_data="bet_range_10_12")
    )
    builder.row(
        types.InlineKeyboardButton(text="1к на 🔴", callback_data="bet_red"),
        types.InlineKeyboardButton(text="1к на ⚫", callback_data="bet_black"),
        types.InlineKeyboardButton(text="1к на 0💚", callback_data="bet_zero")
    )
    builder.row(
        types.InlineKeyboardButton(text="Повторить", callback_data="repeat"),
        types.InlineKeyboardButton(text="Удвоить", callback_data="double"),
        types.InlineKeyboardButton(text="Крутить", callback_data="spin")
    )
    return builder.as_markup()

# --- МИНИРУЛЕТКА ОЮНУ ---
@dp.message(F.text.lower().in_(["рулетка", "miniroulette"]))
async def cmd_roulette(message: types.Message):
    user_id = message.from_user.id
    if user_id not in users_data:
        users_data[user_id] = {
            "balance": 507000, 
            "last_bet_amount": 1000, 
            "current_bet_type": "red", 
            "current_bet_amount": 1000, 
            "bet_name_text": "на красное",
            "roulette_history": [],
            "bandit_history": [],
            "total_won_coins": 0,
            "total_lost_coins": 0
        }
    
    user = users_data[user_id]
    text = (
        f"Минирулетка\n"
        f"Монеты: {user['balance']} 🪙\n"
        "Угадите число из:\n"
        "0💚\n"
        "1🔴 2⚫ 3🔴 4⚫ 5🔴 6⚫\n"
        "7🔴 8⚫ 9🔴 10⚫ 11🔴 12⚫\n\n"
        "Ставки можно текстом:\n"
        "1000 на красное | 5000 на 12 же 100000 к / 100000 ч"
    )
    await message.answer(text, reply_markup=get_roulette_keyboard())

# --- ТЕКСТ АРКЫЛУУ СТАВКА КЫЛУУ ЖАНА АНИМАЦИЯ ---
@dp.message(F.text.regexp(r'^\d+'))
async def text_bet_handler(message: types.Message):
    text = message.text.strip().lower()
    user_id = message.from_user.id
    username = message.from_user.first_name or "Игрок"

    if user_id not in users_data:
        users_data[user_id] = {
            "balance": 507000, 
            "last_bet_amount": 1000, 
            "current_bet_type": "red", 
            "current_bet_amount": 1000, 
            "bet_name_text": "на красное",
            "roulette_history": [],
            "total_won_coins": 0,
            "total_lost_coins": 0
        }

    user = users_data[user_id]

    # Санды жана багытты табуу (мисалы: "100000 к", "100000 ч", "1000 на красное" ж.б.)
    parts = text.split()
    if len(parts) < 2:
        return

    try:
        bet_amt = int(parts[0])
    except ValueError:
        return

    action_text = parts[1]
    bet_type = "red"
    bet_name = "на красное"

    if "к" in action_text or "красн" in action_text:
        bet_type = "red"
        bet_name = "на красное"
    elif "ч" in action_text.lower() or "черн" in action_text:
        bet_type = "black"
        bet_name = "на черное"
    elif action_text == "0" or "зелен" in action_text:
        bet_type = 0
        bet_name = "на 0"
    else:
        # Эгер сан болсо (мисалы: 5000 на 12)
        try:
            bet_type = int(action_text)
            bet_name = f"на {bet_type}"
        except ValueError:
            return

    if user["balance"] < bet_amt:
        await message.answer("❌ Балансыңызда монета жетишсиз!")
        return

    user["balance"] -= bet_amt
    user["current_bet_amount"] = bet_amt
    user["current_bet_type"] = bet_type
    user["bet_name_text"] = bet_name

    # 1. Ставка кабыл алынганын билдирүү
    msg = await message.answer(f"🎲 Ставка принята: <b>{bet_amt}</b> {betname}\n⏳ Рулетка айланып жатат...", parse_mode="HTML")

    # 2. 3 секундтук анимация (эмодзилердин тегерениши)
    animation_frames = [
        "🔄 Рулетка крутится: 🔴 ⚫ 💚 🔴",
        "🔄 Рулетка крутится: 💚 🔴 ⚫ 🔴",
        "🔄 Рулетка крутится: ⚫ 💚 🔴 ⚫"
    ]
    for frame in animation_frames:
        await asyncio.sleep(1)
        try:
            await msg.edit_text(frame)
        except Exception:
            pass

    # 3. Жыйынтык чыгаруу
    rolled_num = random.randint(0, 12)
    rolled_emoji = get_number_emoji(rolled_num)

    is_win = False
    win_mult = 2

    if bet_type == "red" and rolled_num in RED_NUMBERS:
        is_win = True
    elif bet_type == "black" and rolled_num in BLACK_NUMBERS:
        is_win = True
    elif bet_type == 0 and rolled_num == 0:
        is_win = True
        win_mult = 12
    elif isinstance(bet_type, int) and bet_type == rolled_num:
        is_win = True
        win_mult = 12

    result_lines = [
        f"Рулетка: {rolled_num} {rolled_emoji}", 
        f"<b>{username}</b> {bet_amt} {bet_name}"
    ]

    if is_win:
        winnings = bet_amt * win_mult
        user["balance"] += winnings
        user["total_won_coins"] += winnings
        result_lines.append(f"<b>{username}</b> выиграл <b>{winnings}</b> на {rolled_emoji}")
    else:
        user["total_lost_coins"] += bet_amt
        result_lines.append(f"<b>{username}</b> проиграл {bet_amt}")

    user["roulette_history"].insert(0, f"{rolled_num} {rolled_emoji}")
    if len(user["roulette_history"]) > 10:
        user["roulette_history"].pop()

    history_display = "\n".join(user["roulette_history"])
    final_text = "\n".join(result_lines) + f"\n\n<b>История выпадений:</b>\n{history_display}"

    try:
        await msg.edit_text(final_text, parse_mode="HTML")
    except Exception:
        await message.answer(final_text, parse_mode="HTML")

# Кнопка аркылуу крутить кылуу
@dp.callback_query(F.data == "spin")
async def roulette_spin_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    username = callback.from_user.first_name or "Игрок"
    
    if user_id not in users_data:
        users_data[user_id] = {"balance": 507000, "current_bet_amount": 1000, "current_bet_type": "red", "bet_name_text": "на красное", "roulette_history": [], "total_won_coins": 0, "total_lost_coins": 0}
    
    user = users_data[user_id]
    bet_amt = user.get("current_bet_amount", 1000)
    bet_type = user.get("current_bet_type", "red")
    bet_name = user.get("bet_name_text", "на красное")

    if user["balance"] < bet_amt:
        await callback.answer("Балансыңызда монета жетишсиз!", show_alert=True)
        return

    user["balance"] -= bet_amt
    await callback.answer("⏳ Рулетка айланууда...")

    msg = await callback.message.answer(f"🎲 Ставка: <b>{bet_amt}</b> {bet_name}\n⏳ Айланууда...", parse_mode="HTML")
    await asyncio.sleep(3)

    rolled_num = random.randint(0, 12)
    rolled_emoji = get_number_emoji(rolled_num)

    is_win = False
    win_mult = 2
    if bet_type == "red" and rolled_num in RED_NUMBERS:
        is_win = True
    elif bet_type == "black" and rolled_num in BLACK_NUMBERS:
        is_win = True
    elif bet_type == 0 and rolled_num == 0:
        is_win = True
        win_mult = 12

    result_lines = [f"Рулетка: {rolled_num} {rolled_emoji}", f"<b>{username}</b> {bet_amt} {bet_name}"]

    if is_win:
        winnings = bet_amt * win_mult
        user["balance"] += winnings
        user["total_won_coins"] += winnings
        result_lines.append(f"<b>{username}</b> выиграл <b>{winnings}</b> на {rolled_emoji}")
    else:
        user["total_lost_coins"] += bet_amt
        result_lines.append(f"<b>{username}</b> проиграл {bet_amt}")

    user["roulette_history"].insert(0, f"{rolled_num} {rolled_emoji}")
    if len(user["roulette_history"]) > 10:
        user["roulette_history"].pop()

    history_display = "\n".join(user["roulette_history"])
    final_text = "\n".join(result_lines) + f"\n\n<b>История выпадений:</b>\n{history_display}"

    await msg.edit_text(final_text, parse_mode="HTML")

# Баланс ("б")
@dp.message(F.text.lower() == "б")
async def show_balance(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.first_name or "Игрок"
    if user_id not in users_data:
        users_data[user_id] = {"balance": 507000}
    await message.answer(f"<b>{username}</b>\nМонеты: {users_data[user_id]['balance']} 🪙", parse_mode="HTML")

# Админ закреп
@dp.message(F.reply_to_message, F.text.lower() == "закреп")
async def pin_message_admin(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    try:
        await message.reply_to_message.pin()
        await message.answer("📌 Билдирүү закреп кылынды!")
    except Exception as e:
        await message.answer(f"❌ Ката: {e}")

# ID командасы
@dp.message(F.text.lower() == "/id")
async def show_user_id(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.first_name or "Колдонуучу"
    await message.answer(f"👤 <b>{username}</b>, сенин ID номериң:\n🆔 <code>{user_id}</code>", parse_mode="HTML")

async def main():
    print("Бот ишке кирди!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
