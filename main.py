import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, F, types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime

TOKEN = "8981337963:AAG0tCPAwXo1ldR20VMLODwKPKnsBqgdi4Q"

bot = Bot(token=TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

ADMIN_IDS = {7978591176}  

users_data = {}
roulette_history_log = []  # Рулетканын акыркы чыккан сандары (лог үчүн)
bandit_daily_history = []  # Бандит оюнунун күнүмдүк тарыхы

RED_NUMBERS = {1, 3, 5, 7, 9, 11}
BLACK_NUMBERS = {2, 4, 6, 8, 10, 12}

BAD_WORDS = {
    "зайбал", "заебал", "заебался", "котогум", "котокум", "сука", "блять", 
    "блядь", "нахуй", "нахауй", "энендин", "еблан", "далбайоп", 
    "долбоеб", "далбаеб", "пидор", "пидарас", "ебать"
}

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
        types.InlineKeyboardButton(text="Крутить", callback_data="spin")
    )
    return builder.as_markup()

# --- МОДЕРАЦИЯ И АНТИМАТ / БАН В ГРУППАХ ---
@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def group_moderation(message: types.Message, bot: Bot):
    if message.from_user.id in ADMIN_IDS:
        return

    text = message.text or message.caption or ""
    text_lower = text.lower()
    words = text_lower.split()

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
        return

    is_bad = False
    for word in words:
        cleaned_word = "".join(filter(str.isalnum, word))
        if cleaned_word in BAD_WORDS:
            is_bad = True
            break
        for bad in BAD_WORDS:
            if bad in cleaned_word and len(cleaned_word) > 3:
                is_bad = True
                break

    if is_bad:
        try:
            await message.delete()
        except Exception:
            pass
        
        user_name = message.from_user.first_name or "Игрок"
        user_id = message.from_user.id
        chat_id = message.chat.id

        warning_text = (
            f"⚠️ <b>{user_name}</b>, сөгүнгөнүңүз үчүн эскертүү берилип, чаттан четтетилди (Бан)! 🚫"
        )
        try:
            await message.answer(warning_text, parse_mode="HTML")
            # Колдонуучуну чаттан банга салуу
            await bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
        except Exception:
            pass

# --- /START ---
@dp.message(F.text.casefold() == "/start")
async def cmd_start(message: types.Message):
    await message.answer("👋 Бот бардык группаларда активдүү! «Бандит», «Рулетка», «Лог» же «История» деп жазыңыз.")

# --- ПРОФИЛЬ ---
@dp.message(F.text.casefold().in_(["профиль", "мой профиль"]))
async def show_user_profile(message: types.Message):
    user = message.from_user
    user_id = user.id
    username = user.first_name or "Пользователь"

    if user_id not in users_data:
        users_data[user_id] = {
            "balance": 507000, 
            "pending_bets": [],
            "total_won_coins": 0,
            "total_lost_coins": 0
        }

    u_data = users_data[user_id]
    display_balance = "∞ (Безлимит)" if user_id in ADMIN_IDS else f"{u_data['balance']} 🪙"

    profile_text = (
        f"👤 <b>{username}</b>\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"💰 Баланс: {display_balance}\n"
        f"📊 Выиграно: {u_data['total_won_coins']}\n"
        f"📉 Проиграно: {u_data['total_lost_coins']}"
    )
    await message.answer(profile_text, parse_mode="HTML")

# --- АДМИН БАЛАНС ---
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
            "pending_bets": [],
            "total_won_coins": 0,
            "total_lost_coins": 0
        }
    
    users_data[target_user_id]["balance"] += amount
    await message.answer(f"✅ Успешно! Пользователю <code>{target_user_id}</code> начислено <b>{amount}</b> монет.", parse_mode="HTML")

# --- ИГРА «БАНДИТ» ---
@dp.message(F.text.casefold().in_(["бандит", "слоты", "slot"]))
async def slot_bandit_game(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.first_name or "Игрок"

    if user_id not in users_data:
        users_data[user_id] = {
            "balance": 507000, 
            "pending_bets": [],
            "total_won_coins": 0,
            "total_lost_coins": 0
        }

    user = users_data[user_id]
    bet_cost = 1000  

    if user_id not in ADMIN_IDS and user["balance"] < bet_cost:
        await message.answer("❌ Недостаточно монет для игры в «Бандит» (нужно минимум 1000)!")
        return

    if user_id not in ADMIN_IDS:
        user["balance"] -= bet_cost

    msg = await message.answer(f"💎 <b>{username}</b>\n\n⬜ ⬜ ⬜ ⬜ ⬜", parse_mode="HTML")
    await asyncio.sleep(0.8)

    possible_symbols = ["♠️", "🀄", "♣️", "♦️", "♥️"]
    res_symbols = [random.choice(possible_symbols) for _ in range(5)]

    current_display = ["⬜", "⬜", "⬜", "⬜", "⬜"]
    for i in range(5):
        current_display[i] = res_symbols[i]
        display_str = " ".join(current_display)
        try:
            await msg.edit_text(f"💎 <b>{username}</b>\n\n{display_str}", parse_mode="HTML")
        except Exception:
            pass
        await asyncio.sleep(0.4)

    counts = Counter(res_symbols)
    win_amount = 0
    result_text = ""

    if counts["♥️"] >= 3 or counts["♦️"] >= 3 or counts["♠️"] >= 3 or counts["♣️"] >= 3 or counts["🀄"] >= 3:
        # Утуш 3000дон 60000ге чейин кокус чыгат
        win_amount = random.randint(3, 60) * 1000
        matched_symbol = [sym for sym, count in counts.items() if count >= 3][0]
        result_text = f"Выигрыш: {win_amount} 🪙"
    else:
        result_text = f"Проигрыш: 1000 🪙"

    final_display = " ".join(res_symbols)

    if win_amount > 0:
        user["balance"] += win_amount
        user["total_won_coins"] += win_amount
        bandit_record = f"👤 {username} | 🎰 Бандит: +{win_amount} 🪙 ({final_display})"
    else:
        user["total_lost_coins"] += bet_cost
        bandit_record = f"👤 {username} | 🎰 Бандит: -1000 🪙 ({final_display})"

    # Күнүмдүк бандит тарыхына кошуу
    bandit_daily_history.insert(0, bandit_record)
    if len(bandit_daily_history) > 30:
        bandit_daily_history.pop()

    final_text_str = (
        f"💎 <b>{username}</b>\n\n"
        f"{final_display}\n\n"
        f"<b>{result_text}</b>"
    )
    try:
        await msg.edit_text(final_text_str, parse_mode="HTML")
    except Exception:
        await message.answer(final_text_str, parse_mode="HTML")

# --- РУЛЕТКА ---
@dp.message(F.text.casefold().in_(["рулетка", "miniroulette"]))
async def cmd_roulette(message: types.Message):
    user_id = message.from_user.id
    if user_id not in users_data:
        users_data[user_id] = {
            "balance": 507000, 
            "pending_bets": [],
            "total_won_coins": 0,
            "total_lost_coins": 0
        }
    
    user = users_data[user_id]
    display_balance = "∞ (Безлимит)" if user_id in ADMIN_IDS else user['balance']
    
    text = (
        f"🎰 Рулетка\n"
        f"Монеты: {display_balance} 🪙\n"
        "Ставка мисалы: 5000 2 же 30000 к"
    )
    await message.answer(text, reply_markup=get_roulette_keyboard())

# --- СТАВКИ В РУЛЕТКЕ ---
@dp.message(F.text.casefold().regexp(r'^(ва\s*банк|\d+)\s+([0-12]|[кчз]|на\s+(красное|черное|зеленое))'))
async def save_bet_handler(message: types.Message):
    text = message.text.strip().casefold()
    user_id = message.from_user.id
    username = message.from_user.first_name or "Игрок"

    if user_id not in users_data:
        users_data[user_id] = {
            "balance": 507000, 
            "pending_bets": [],
            "total_won_coins": 0,
            "total_lost_coins": 0
        }

    user = users_data[user_id]
    parts = text.split()
    if len(parts) < 2:
        return

    if "банк" in parts[0] or "ва" in parts[0]:
        bet_amt = 100000 if user_id in ADMIN_IDS else user["balance"]
        if bet_amt <= 0:
            return
        target = parts[-1]
    else:
        try:
            bet_amt = int(parts[0])
        except ValueError:
            return
        target = parts[1]

    bet_type = None
    bet_desc = ""

    if target.isdigit():
        num_val = int(target)
        if 0 <= num_val <= 12:
            bet_type = f"num_{num_val}"
            bet_desc = f"на {num_val}"
        else:
            return
    else:
        if target in ["к", "красное"] or "красн" in text:
            bet_type = "red"
            bet_desc = "на красное"
        elif target in ["ч", "черное"] or "черн" in text:
            bet_type = "black"
            bet_desc = "на черное"
        elif target in ["з", "зеленое"] or "зелен" in text:
            bet_type = 0
            bet_desc = "на зеленое"
        else:
            return

    if user_id not in ADMIN_IDS and user["balance"] < bet_amt:
        await message.answer(f"❌ <b>{username}</b>, недостаточно монет!", parse_mode="HTML")
        return

    user["pending_bets"].append({
        "amount": bet_amt,
        "type": bet_type,
        "desc": bet_desc,
        "raw_target": target
    })

    display_amount = "ВА БАНК" if ("банк" in text or "ва" in text) else str(bet_amt)
    await message.answer(f"✅ <b>{username}</b> 🕊 Ставка принята: {display_amount} на {target}", parse_mode="HTML")

# --- ЗАПУСК РУЛЕТКИ («ГО») С ЖИДКОЙ GIF АНИМАЦИЕЙ ---
@dp.message(F.text.casefold() == "го")
async def start_game_handler(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.first_name or "Игрок"

    if user_id not in users_data or not users_data[user_id].get("pending_bets"):
        await message.answer(f"⚠️ <b>{username}</b>, сначала сделайте ставки!", parse_mode="HTML")
        return

    user_data_dict = users_data[user_id]
    bets = user_data_dict["pending_bets"]
    total_bet_amt = sum(b["amount"] for b in bets)

    if user_id not in ADMIN_IDS and user_data_dict["balance"] < total_bet_amt:
        await message.answer(f"❌ <b>{username}</b>, недостаточно монет!", parse_mode="HTML")
        user_data_dict["pending_bets"] = []
        return

    if user_id not in ADMIN_IDS:
        user_data_dict["balance"] -= total_bet_amt
    
    user_data_dict["pending_bets"] = []

    # Казино анимациясы 3 секунд
    spin_msg = await message.answer("🎰 🎲 Рулетка крутится... 3 секунда...")
    await asyncio.sleep(3)
    
    try:
        await spin_msg.delete()
    except Exception:
        pass

    rolled_num = random.randint(0, 12)
    rolled_emoji = get_number_emoji(rolled_num)

    # Рулетка логуна кошуу (сүрөттөгүдөй столбик кылып сактоо үчүн)
    roulette_history_log.insert(0, f"{rolled_num} {rolled_emoji}")
    if len(roulette_history_log) > 10:
        roulette_history_log.pop()

    result_lines = [
        f"🎰 Рулетка: {rolled_num} {rolled_emoji}"
    ]

    total_winnings = 0
    total_loss = total_bet_amt

    for bet in bets:
        bet_amt = bet["amount"]
        b_type = bet["type"]
        raw_t = bet["raw_target"]
        
        result_lines.append(f"<b>{username}</b> 🕊 {bet_amt} на {raw_t}")

        is_win = False
        mult = 0

        if str(b_type).startswith("num_"):
            target_n = int(b_type.split("_")[1])
            if rolled_num == target_n:
                is_win = True
                mult = 12
        elif b_type == "red" and rolled_num in RED_NUMBERS:
            is_win = True
            mult = 2
        elif b_type == "black" and rolled_num in BLACK_NUMBERS:
            is_win = True
            mult = 2
        elif b_type == 0 and rolled_num == 0:
            is_win = True
            mult = 12

        if is_win:
            win_val = bet_amt * mult
            total_winnings += win_val

    if total_winnings > 0:
        user_data_dict["balance"] += total_winnings
        user_data_dict["total_won_coins"] += total_winnings
        result_lines.append(f"\n🎉 <b>{username}</b> выиграл: {total_winnings} 🪙")
    else:
        user_data_dict["total_lost_coins"] += total_loss
        result_lines.append(f"\n❌ <b>{username}</b> проиграл {total_loss} 🪙")

    final_text = "\n".join(result_lines)
    await message.answer(final_text, parse_mode="HTML")

# --- ЛОГ (ТАК СҮРӨТТӨГҮДӨЙ СТОЛБИК ТҮРҮНДӨ) ---
@dp.message(F.text.casefold() == "лог")
async def show_roulette_log(message: types.Message):
    if not roulette_history_log:
        await message.answer("📜 Рулетка логу азырынча бош!")
        return
    
    log_output = "\n".join(roulette_history_log)
    await message.answer(log_output, parse_mode="HTML")

# --- ИСТОРИЯ (БАНДИТ ОЙУНУНУН КҮНҮМДҮК ЖЫЙЫНТЫГЫ АТЫ МЕНЕН) ---
@dp.message(F.text.casefold() == "история")
async def show_bandit_history(message: types.Message):
    if not bandit_daily_history:
        await message.answer("📜 Бүгүнкү бандит оюндарынын тарыхы бош!")
        return

    history_output = "📜 <b>Бандит оюнунун күнүмдүк тарыхы:</b>\n\n" + "\n".join(bandit_daily_history)
    await message.answer(history_output, parse_mode="HTML")

# --- БАЛАНС («б») ---
@dp.message(F.text.casefold() == "б")
async def show_balance(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.first_name or "Игрок"
    if user_id not in users_data:
        users_data[user_id] = {"balance": 507000}
    
    disp_bal = "∞ (Безлимит)" if user_id in ADMIN_IDS else users_data[user_id]['balance']
    await message.answer(f"<b>{username}</b>\nМонеты: {disp_bal} 🪙", parse_mode="HTML")

async def main():
    print("Бот иштеп жатат!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
