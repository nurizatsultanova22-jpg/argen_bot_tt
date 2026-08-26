import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, F, types
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = "8981337963:AAG0tCPAwXo1ldR20VMLODwKPKnsBqgdi4Q"

bot = Bot(token=TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

# Сиздин ID'ңиз админ катары
ADMIN_IDS = {7978591176}  

users_data = {}
global_records = {
    "max_win": {"name": "Жок", "amount": 0},
    "max_loss": {"name": "Жок", "amount": 0}
}

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

# --- ШИЛТЕЛЕМЕЛЕРДИ БӨГӨТТӨӨ (Тек гана группалар үчүн) ---
@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def anti_spam_links(message: types.Message):
    if message.from_user.id in ADMIN_IDS:
        return

    text = message.text or message.caption or ""
    text_lower = text.lower()

    has_link = "t.me/" in text_lower or "http://" in text_lower or "https://" in text_lower or "@" in text_lower
    
    if message.entities:
        for entity in message.entities:
            if entity.type in ["url", "text_link", "mention"]:
                has_link = True

    if has_link:
        try:
            await message.delete()
        except Exception:
            pass

# --- /START КОМАНДАСЫ ---
@dp.message(F.text.lower() == "/start")
async def cmd_start(message: types.Message):
    await message.answer("👋 Саламатсызбы! Бот иштеп жатат. «Рулетка» деп жазып оюнду баштасаңыз болот.")

# --- ID КОМАНДАСЫ ---
@dp.message(F.text.lower() == "/id")
async def show_user_id(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.first_name or message.from_user.username or "Пользователь"
    await message.answer(f"👤 <b>{username}</b>, ваш ID:\n🆔 <code>{user_id}</code>", parse_mode="HTML")

# --- АДМИН БАЛАНС КОШУУ (+ ID СУММА) ---
@dp.message(F.text.regexp(r'^\+\s*\d+\s+\d+'))
async def add_coins_by_admin(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    parts = message.text.split()
    if len(parts) < 3:
        return
    
    target_user_id = int(parts[1])
    amount = int(parts[2])

    if target_user_id not in users_data:
        users_data[target_user_id] = {
            "balance": 507000, 
            "roulette_history": [],
            "pending_bet": None,
            "total_won_coins": 0,
            "total_lost_coins": 0
        }
    
    users_data[target_user_id]["balance"] += amount
    await message.answer(f"✅ Успешно! Пользователю <code>{target_user_id}</code> начислено <b>{amount}</b> монет.", parse_mode="HTML")

# --- РУЛЕТКА МЕНЮСҮ ---
@dp.message(F.text.lower().in_(["рулетка", "miniroulette"]))
async def cmd_roulette(message: types.Message):
    user_id = message.from_user.id
    if user_id not in users_data:
        users_data[user_id] = {
            "balance": 507000, 
            "roulette_history": [],
            "pending_bet": None,
            "total_won_coins": 0,
            "total_lost_coins": 0
        }
    
    user = users_data[user_id]
    display_balance = "∞ (Безлимит)" if user_id in ADMIN_IDS else user['balance']
    
    text = (
        f"Минирулетка\n"
        f"Монеты: {display_balance} 🪙\n"
        "Угадите число из:\n"
        "0💚\n"
        "1🔴 2⚫ 3🔴 4⚫ 5🔴 6⚫\n"
        "7🔴 8⚫ 9🔴 10⚫ 11🔴 12⚫\n\n"
        "Ставки текстом:\n"
        "• 30000 к (на красное)\n"
        "• 30000 ч (на черное)\n"
        "• 30000 з (на зеленое)"
    )
    await message.answer(text, reply_markup=get_roulette_keyboard())

# --- 1. СТАВКА ЖАЗГАНДА ---
@dp.message(F.text.regexp(r'^\d+\s*([кчзКЧЗ]|на\s+(красное|черное|зеленое))'))
async def save_bet_handler(message: types.Message):
    text = message.text.strip().lower()
    user_id = message.from_user.id

    if user_id not in users_data:
        users_data[user_id] = {
            "balance": 507000, 
            "roulette_history": [],
            "pending_bet": None,
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

    if side == "к" or "красное" in text:
        bet_type = "red"
        bet_name = "на красное"
    elif side == "ч" or "черное" in text:
        bet_type = "black"
        bet_name = "на черное"
    elif side == "з" or "зеленое" in text:
        bet_type = 0
        bet_name = "на зеленое"
    else:
        return

    if user_id not in ADMIN_IDS and user["balance"] < bet_amt:
        await message.answer("❌ У вас недостаточно монет на балансе!")
        return

    user["pending_bet"] = {
        "amount": bet_amt,
        "type": bet_type,
        "name": bet_name
    }

    await message.answer(f"Ставка принята: <b>{bet_amt}</b> {bet_name}\nНапишите <b>«го»</b> для запуска!", parse_mode="HTML")

# --- 2. «ГО» ДЕП ЖАЗГАНДА ОЮНДУ БАШТОО ---
@dp.message(F.text.lower() == "го")
async def start_game_handler(message: types.Message):
    user_id = message.from_user.id
    user = message.from_user
    username = user.first_name or user.username or f"Игрок_{user_id}"

    if user_id not in users_data or not users_data[user_id].get("pending_bet"):
        await message.answer("⚠️ Сначала сделайте ставку (например: 30000 к)!")
        return

    user_data_dict = users_data[user_id]
    bet_info = user_data_dict["pending_bet"]
    bet_amt = bet_info["amount"]
    bet_type = bet_info["type"]
    bet_name = bet_info["name"]

    if user_id not in ADMIN_IDS and user_data_dict["balance"] < bet_amt:
        await message.answer("❌ У вас недостаточно монет на балансе!")
        user_data_dict["pending_bet"] = None
        return

    if user_id not in ADMIN_IDS:
        user_data_dict["balance"] -= bet_amt
    user_data_dict["pending_bet"] = None

    msg = await message.answer(f"🎲 Ставка: <b>{bet_amt}</b> {bet_name}\n⏳ До начала: 3...", parse_mode="HTML")
    await asyncio.sleep(1)
    try:
        await msg.edit_text(f"🎲 Ставка: <b>{bet_amt}</b> {bet_name}\n⏳ До начала: 2...", parse_mode="HTML")
    except Exception:
        pass
    await asyncio.sleep(1)
    try:
        await msg.edit_text(f"🎲 Ставка: <b>{bet_amt}</b> {bet_name}\n⏳ До начала: 1...", parse_mode="HTML")
    except Exception:
        pass
    await asyncio.sleep(1)

    try:
        await msg.delete()
    except Exception:
        pass

    gif_url = "https://media.giphy.com/media/3o7TKSjRrfIPjeiVyM/giphy.gif"
    gif_msg = await message.answer_animation(animation=gif_url, caption="🎲 <b>ZERO</b> | Кости крутятся...", parse_mode="HTML")

    await asyncio.sleep(3)

    try:
        await gif_msg.delete()
    except Exception:
        pass

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

    # Тарыхка кошуу (вертикалдык столбик үчүн)
    user_data_dict["roulette_history"].insert(0, f"{rolled_num} {rolled_emoji}")
    if len(user_data_dict["roulette_history"]) > 10:
        user_data_dict["roulette_history"].pop()

    result_lines = [
        f"Рулетка: {rolled_num} {rolled_emoji}",
        f"<b>{username}</b> {bet_amt} {bet_name}"
    ]

    if is_win:
        winnings = bet_amt * win_mult
        user_data_dict["balance"] += winnings
        user_data_dict["total_won_coins"] += winnings
        result_lines.append(f"<b>{username}</b> выиграл {winnings} на {rolled_emoji}")

        if winnings > global_records["max_win"]["amount"]:
            global_records["max_win"] = {"name": username, "amount": winnings}
    else:
        user_data_dict["total_lost_coins"] += bet_amt
        result_lines.append(f"<b>{username}</b> проиграл {bet_amt} на {rolled_emoji}")

        if bet_amt > global_records["max_loss"]["amount"]:
            global_records["max_loss"] = {"name": username, "amount": bet_amt}

    # Скриншоттогудай вертикалдык логду жыйынтыктын астына кошуу
    history = user_data_dict["roulette_history"]
    history_display = "\n".join([f"{item}" for item in history])
    
    final_text = "\n".join(result_lines) + "\n\n📜 <b>Лог истории:</b>\n" + history_display
    await message.answer(final_text, parse_mode="HTML")

# --- РЕКОРД КОМАНДАСЫ ---
@dp.message(F.text.lower() == "рекорд")
async def show_records(message: types.Message):
    win_record = global_records["max_win"]
    loss_record = global_records["max_loss"]

    text = (
        "📊 <b>Глобальный рекорд дня (топ)</b>\n\n"
        f"🥇 <b>{win_record['name']}</b> — {win_record['amount']} монет (рекорд выигрыша)\n"
        f"🥉 <b>{loss_record['name']}</b> — {loss_record['amount']} монет (рекорд проигрыша)\n\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "🎁 <b>Призы на сегодня</b>\n"
        "Выплата в 00:00 (Москва)"
    )
    await message.answer(text, parse_mode="HTML")

# --- «ЛОГ» ЖЕ «ИСТОРИЯ» ---
@dp.message(F.text.lower().in_(["лог", "история"]))
async def show_game_logs(message: types.Message):
    user_id = message.from_user.id
    if user_id not in users_data or not users_data[user_id]["roulette_history"]:
        await message.answer("📜 История игр пуста.")
        return

    history = users_data[user_id]["roulette_history"]
    history_display = "\n".join([f"{item}" for item in history])
    
    await message.answer(history_display, parse_mode="HTML")

# Баланс («б»)
@dp.message(F.text.lower() == "б")
async def show_balance(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.first_name or message.from_user.username or "Игрок"
    if user_id not in users_data:
        users_data[user_id] = {"balance": 507000}
    
    disp_bal = "∞ (Безлимит)" if user_id in ADMIN_IDS else users_data[user_id]['balance']
    await message.answer(f"<b>{username}</b>\nМонеты: {disp_bal} 🪙", parse_mode="HTML")

# --- АДМИН ЗАКРЕП ---
@dp.message(F.reply_to_message, F.text.lower() == "закреп")
async def pin_message_admin(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    try:
        await message.reply_to_message.pin()
        await message.answer("📌 Сообщение успешно закреплено!")
    except Exception as e:
        await message.answer(f"❌ Ошибка закрепления: {e}")

async def main():
    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
