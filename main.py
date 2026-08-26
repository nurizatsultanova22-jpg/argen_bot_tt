import asyncio
import logging
import random
from datetime import datetime
from aiogram import Bot, Dispatcher, F, types
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = "8981337963:AAG0tCPAwXo1ldR20VMLODwKPKnsBqgdi4Q"

bot = Bot(token=TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

# Өзүңүздүн Telegram ID'ңизди ушул жерге жазыңыз (админ үчүн)
ADMIN_IDS = {123456789}  # <-- Өзүңүздүн ID менен алмаштырыңыз!

# Бардык оюнчулардын маалыматтары
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
        "1000 на красное | 5000 на 12"
    )
    await message.answer(text, reply_markup=get_roulette_keyboard())

# Кнопкалар менен иштөө (Рулетка үчүн Callback)
@dp.callback_query(F.data.startswith("bet_") | F.data.in_(["repeat", "double", "spin"]))
async def roulette_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    username = callback.from_user.first_name or "Игрок"
    
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
    data = callback.data

    if data == "bet_red":
        user["current_bet_type"] = "red"
        user["current_bet_amount"] = 1000
        user["bet_name_text"] = "на красное"
        await callback.answer("Ставка выбрана: 1000 на красное")
        return
    elif data == "bet_black":
        user["current_bet_type"] = "black"
        user["current_bet_amount"] = 1000
        user["bet_name_text"] = "на черное"
        await callback.answer("Ставка выбрана: 1000 на черное")
        return
    elif data == "bet_zero":
        user["current_bet_type"] = 0
        user["current_bet_amount"] = 1000
        user["bet_name_text"] = "на 0"
        await callback.answer("Ставка выбрана: 1000 на 0")
        return
    elif data == "spin":
        bet_amt = user.get("current_bet_amount", 1000)
        bet_type = user.get("current_bet_type", "red")
        bet_name = user.get("bet_name_text", "на красное")

        if user["balance"] < bet_amt:
            await callback.answer("Балансыңызда монета жетишсиз!", show_alert=True)
            return

        user["balance"] -= bet_amt
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

        result_lines = [f"Рулетка: {rolled_num} {rolled_emoji}", f"{username} {bet_amt} {bet_name}"]

        if is_win:
            winnings = bet_amt * win_mult
            user["balance"] += winnings
            user["total_won_coins"] += winnings
            result_lines.append(f"{username} выиграл {winnings} на {rolled_emoji}")
        else:
            user["total_lost_coins"] += bet_amt
            result_lines.append(f"{username} проиграл {bet_amt}")

        # Акыркы чыккан сан жана түстөрдү сактоо (сүрөттөгүдөй тизме үчүн)
        user["roulette_history"].insert(0, f"{rolled_num} {rolled_emoji}")
        if len(user["roulette_history"]) > 10:
            user["roulette_history"].pop()

        history_display = "\n".join(user["roulette_history"])
        final_text = "\n".join(result_lines) + f"\n\n<b>История выпадений:</b>\n{history_display}"

        await callback.message.answer(final_text, parse_mode="HTML")
        await callback.answer()

# --- БАНДИТ (СЛОТ) ОЮНУ ---
@dp.message(F.text.lower().in_(["бандит", "слот", "bandit"]))
async def cmd_bandit(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.first_name or "Игрок"
    
    if user_id not in users_data:
        users_data[user_id] = {"balance": 507000, "bandit_history": [], "total_won_coins": 0, "total_lost_coins": 0}
    
    user = users_data[user_id]
    cost = 1000

    if user["balance"] < cost:
        await message.answer("❌ Балансыңызда бандит ойноо үчүн монета жетишсиз! (Керек: 1000 🪙)")
        return

    user["balance"] -= cost
    symbols = ["♥️", "♦️", "♠️", "🎴", "🀄"]
    slot1, slot2, slot3, slot4 = random.choice(symbols), random.choice(symbols), random.choice(symbols), random.choice(symbols)

    slot_board = (
        f"🎰 <b>БАНДИТ ОЮНУ</b> 🎰\n\n"
        f" ┌─────────┐\n"
        f" │ {slot1} │ {slot2} │\n"
        f" ├─────────┤\n"
        f" │ {slot3} │ {slot4} │\n"
        f" └─────────┘\n\n"
    )

    all_symbols = [slot1, slot2, slot3, slot4]
    win_amount = 0
    win_desc = ""

    if all_symbols.count("🎴") == 4:
        win_amount, win_desc = 70000, "🔥 4x 🎴 чыкты! Утуш: 70,000 монет!"
    elif all_symbols.count("♥️") == 4:
        win_amount, win_desc = 15000, "💖 4x Жүрөк (♥️) чыкты! Утуш: 15,000 монет!"
    elif all_symbols.count("🀄") >= 3:
        win_amount, win_desc = 10000, "🀄 3x 🀄 чыкты! Утуш: 10,000 монет!"
    elif all_symbols.count("♦️") >= 3:
        win_amount, win_desc = 6000, "♦️ 3x Бриллиант чыкты! Утуш: 6,000 монет!"
    elif all_symbols.count("♥️") >= 3:
        win_amount, win_desc = 3000, "♥️ 3x Жүрөк чыкты! Утуш: 3,000 монет!"
    elif all_symbols.count("♠️") >= 3:
        win_amount, win_desc = 3000, "♠️ 3x Пика чыкты! Утуш: 3,000 монет!"

    if win_amount > 0:
        user["balance"] += win_amount
        user["total_won_coins"] += win_amount
        result_text = f"{slot_board}🎉 <b>{username}</b>, куттуктайбыз! {win_desc}\n💰 Баланс: {user['balance']} 🪙"
    else:
        user["total_lost_coins"] += cost
        result_text = f"{slot_board}❌ <b>{username}</b>, бул жолу утулган жоксуз (-1000 🪙).\n💰 Баланс: {user['balance']} 🪙"

    await message.answer(result_text, parse_mode="HTML")

# Балансты көрүү ("б")
@dp.message(F.text.lower() == "б")
async def show_balance(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.first_name or "Игрок"
    if user_id not in users_data:
        users_data[user_id] = {"balance": 507000}
    await message.answer(f"<b>{username}</b>\nМонеты: {users_data[user_id]['balance']} 🪙", parse_mode="HTML")

# Админ закреп кылуу
@dp.message(F.reply_to_message, F.text.lower() == "закреп")
async def pin_message_admin(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    try:
        await message.reply_to_message.pin()
        await message.answer("📌 Билдирүү ийгиликтүү закреп кылынды!")
    except Exception as e:
        await message.answer(f"❌ Ката кетти: {e}")

# "/id" командасы
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
