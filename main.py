import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, F, types
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = "8981337963:AAG0tCPAwXo1ldR20VMLODwKPKnsBqgdi4Q"

bot = Bot(token=TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

ADMIN_IDS = {123456789}  # <-- Өзүңүздүн админ ID'ңизди жазыңыз

users_data = {}

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

# --- РУЛЕТКА МЕНЮСҮ ---
@dp.message(F.text.lower().in_(["рулетка", "miniroulette"]))
async def cmd_roulette(message: types.Message):
    user_id = message.from_user.id
    if user_id not in users_data:
        users_data[user_id] = {
            "balance": 507000, 
            "roulette_history": [],
            "total_won_coins": 0,
            "total_lost_coins": 0
        }
    
    user = users_data[user_id]
    text = (
        f"🎰 <b>Мини-рулетка</b>\n"
        f"💰 Монеты: {user['balance']} 🪙\n\n"
        "Числа:\n"
        "0💚\n"
        "1🔴 2⚫ 3🔴 4⚫ 5🔴 6⚫\n"
        "7🔴 8⚫ 9🔴 10⚫ 11🔴 12⚫\n\n"
        "✍️ <i>Сделайте ставку текстом:</i>\n"
        "<code>100000 к</code> (на красное)\n"
        "<code>50000 ч</code> (на черное)\n"
        "<code>10000 з</code> (на зеленое/0)\n\n"
        "📜 Напишите <b>«лог»</b>, чтобы посмотреть историю игр."
    )
    await message.answer(text, reply_markup=get_roulette_keyboard(), parse_mode="HTML")

# --- СТАВКА ТЕКСТОМ ЖАНА АНИМАЦИЯ ---
@dp.message(F.text.regexp(r'^\d+\s*[кчзКЧЗ]'))
async def text_bet_handler(message: types.Message):
    text = message.text.strip().lower()
    user_id = message.from_user.id
    username = message.from_user.first_name or "Игрок"

    if user_id not in users_data:
        users_data[user_id] = {
            "balance": 507000, 
            "roulette_history": [],
            "total_won_coins": 0,
            "total_lost_coins": 0
        }

    user = users_data[user_id]

    parts = text.split()
    if len(parts) < 2:
        return

    try:
        bet_amt = int(parts[0])
    except ValueError:
        return

    side = parts[1]
    bet_type = "red"
    bet_name = "на красное"

    if "к" in side:
        bet_type = "red"
        bet_name = "на красное"
    elif "ч" in side:
        bet_type = "black"
        bet_name = "на черное"
    elif "з" in side:
        bet_type = 0
        bet_name = "на зеленое (0)"
    else:
        return

    if user["balance"] < bet_amt:
        await message.answer("❌ У вас недостаточно монет на балансе!")
        return

    user["balance"] -= bet_amt

    # 1. Ставка кабыл алынганы тууралуу билдирүү
    accept_msg = await message.answer(f"🎲 Ставка принята: <b>{bet_amt}</b> {bet_name}\n⏳ Ожидание 3 секунды...", parse_mode="HTML")

    # 3 секунд күтүү
    await asyncio.sleep(3)

    try:
        await accept_msg.delete()
    except Exception:
        pass

    # 2. "ZERO" таш/кубик анимациясын көрсөтүү
    await message.answer("🎲 <b>ZERO</b> | Бросаем кости...", parse_mode="HTML")
    dice_msg = await message.answer_dice(emoji="🎲")
    
    # Таштар ойнолуп бүткөнчө дагы 3 секунд күтүү
    await asyncio.sleep(3)

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

    result_lines = [
        f"🎯 <b>Результат рулетки:</b> {rolled_num} {rolled_emoji}",
        f"👤 <b>{username}</b> поставил {bet_amt} {bet_name}"
    ]

    if is_win:
        winnings = bet_amt * win_mult
        user["balance"] += winnings
        user["total_won_coins"] += winnings
        result_lines.append(f"🎉 <b>{username}</b> выиграл <b>{winnings}</b> 🪙 {rolled_emoji}")
    else:
        user["total_lost_coins"] += bet_amt
        result_lines.append(f"😢 <b>{username}</b> проиграл {bet_amt} 🪙")

    # Тарыхка сактоо (максимум 15 элемент)
    user["roulette_history"].insert(0, f"{rolled_num} {rolled_emoji}")
    if len(user["roulette_history"]) > 15:
        user["roulette_history"].pop()

    final_text = "\n".join(result_lines) + f"\n\n💰 Баланс: {user['balance']} 🪙\n💡 <i>Чтобы посмотреть лог (историю), напишите слово <b>«лог»</b></i>"
    await message.answer(final_text, parse_mode="HTML")

# --- «ЛОГ» ДЕП ЖАЗГАНДА ГАНА ТАРЫХТЫ КӨРСӨТҮҮ ---
@dp.message(F.text.lower() == "лог")
async def show_game_logs(message: types.Message):
    user_id = message.from_user.id
    if user_id not in users_data or not users_data[user_id]["roulette_history"]:
        await message.answer("📜 История игр пуста. Сделайте ставку!")
        return

    history = users_data[user_id]["roulette_history"]
    # Сүрөттөгүдөй вертикалдуу форматта чыгаруу
    history_display = "\n".join(history)
    
    log_text = f"📜 <b>История выпадений (Лог):</b>\n\n{history_display}"
    await message.answer(log_text, parse_mode="HTML")

# Балансы текшерүү («б» же «баланс»)
@dp.message(F.text.lower().in_(["б", "баланс"]))
async def show_balance(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.first_name or "Игрок"
    if user_id not in users_data:
        users_data[user_id] = {"balance": 507000}
    await message.answer(f"👤 <b>{username}</b>\n💰 Монеты: {users_data[user_id]['balance']} 🪙", parse_mode="HTML")

# Админ закреп
@dp.message(F.reply_to_message, F.text.lower() == "закреп")
async def pin_message_admin(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    try:
        await message.reply_to_message.pin()
        await message.answer("📌 Сообщение успешно закреплено!")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

# ID командасы
@dp.message(F.text.lower() == "/id")
async def show_user_id(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.first_name or "Пользователь"
    await message.answer(f"👤 <b>{username}</b>, ваш ID:\n🆔 <code>{user_id}</code>", parse_mode="HTML")

async def main():
    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
