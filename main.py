import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, F, types
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from collections import Counter

TOKEN = "8981337963:AAG0tCPAwXo1ldR20VMLODwKPKnsBqgdi4Q"

bot = Bot(token=TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

ADMIN_IDS = {7978591176}  

users_data = {}
roulette_history_log = []  
bandit_daily_history = []  

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

def get_main_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.row(
        types.KeyboardButton(text="🎰 Рулетка"),
        types.KeyboardButton(text="💎 Бандит")
    )
    builder.row(
        types.KeyboardButton(text="💳 Донат"),
        types.KeyboardButton(text="📊 Рекорд"),
        types.KeyboardButton(text="📜 История")
    )
    return builder.as_markup(resize_keyboard=True)

def get_roulette_inline_keyboard():
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
        types.InlineKeyboardButton(text="Крутить (Го)", callback_data="spin")
    )
    return builder.as_markup()

# --- МОДЕРАЦИЯ И ССЫЛКИ / АНТИМАТ В ГРУППАХ ---
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
            "<b>ZERO 🎰🇰🇬</b>\n\n"
            f"⚠️ <b>{user_name}</b>, за мат вы получили предупреждение и были заблокированы! 🚫"
        )
        try:
            await message.answer(warning_text, parse_mode="HTML")
            await bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
        except Exception:
            pass

# --- /START ---
@dp.message(F.text.casefold() == "/start")
async def cmd_start(message: types.Message):
    await message.answer(
        "<b>ZERO 🎰🇰🇬</b>\n\n👋 Бот активен! Используйте кнопки ниже для игры.",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )

# --- ДОНАТ КНОПКА ---
@dp.message(F.text.casefold().in_(["💳 донат", "донат"]))
async def donation_info(message: types.Message):
    donate_text = (
        "<b>ZERO 🎰🇰🇬 | Покупка монет (Донат)</b>\n\n"
        "Для пополнения баланса переведите средства через бота:\n"
        "👉 https://t.me/Zerokassa\n\n"
        "<b>Тарифы:</b>\n"
        "• 200.000 🪙 — 100 сом\n"
        "• 500.000 🪙 — 230 сом\n"
        "• 1.000.000 🪙 — 330 сом\n"
        "• 2.000.000 🪙 — 530 сом\n"
        "• 5.000.000 🪙 — 800 сом\n"
        "• 10.000.000 🪙 — 1000 сом"
    )
    await message.answer(donate_text, parse_mode="HTML", reply_markup=get_main_keyboard())

# --- ПРОФИЛЬ / БАЛАНС (Б ПО ИЛИ ВА БАНК) ---
@dp.message(F.text.casefold().in_(["б", "в", "ва банк", "профиль", "мой профиль"]))
async def show_user_profile(message: types.Message):
    user = message.from_user
    user_id = user.id
    username = user.first_name or "Игрок"

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
        "<b>ZERO 🎰🇰🇬</b>\n\n"
        f"👤 <b>{username}</b>\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"💰 Монеты: {display_balance}\n"
        f"📊 Выиграно: {u_data['total_won_coins']}\n"
        f"📉 Проиграно: {u_data['total_lost_coins']}"
    )
    await message.answer(profile_text, parse_mode="HTML", reply_markup=get_main_keyboard())

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
    await message.answer(f"<b>ZERO 🎰🇰🇬</b>\n\n✅ Пользователю <code>{target_user_id}</code> начислено <b>{amount}</b> монет.", parse_mode="HTML")

# --- ИГРА «БАНДИТ» ---
@dp.message(F.text.casefold().in_(["💎 бандит", "бандит", "слоты", "slot"]))
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
        await message.answer("<b>ZERO 🎰🇰🇬</b>\n\n❌ Недостаточно монет для игры в «Бандит» (нужно минимум 1000)!", parse_mode="HTML")
        return

    if user_id not in ADMIN_IDS:
        user["balance"] -= bet_cost

    msg = await message.answer(f"<b>ZERO 🎰🇰🇬</b>\n\n💎 <b>{username}</b>\n\n⬜ ⬜ ⬜ ⬜ ⬜", parse_mode="HTML")
    await asyncio.sleep(0.8)

    possible_symbols = ["♠️", "🀄", "♣️", "♦️", "♥️"]
    res_symbols = [random.choice(possible_symbols) for _ in range(5)]

    current_display = ["⬜", "⬜", "⬜", "⬜", "⬜"]
    for i in range(5):
        current_display[i] = res_symbols[i]
        display_str = " ".join(current_display)
        try:
            await msg.edit_text(f"<b>ZERO 🎰🇰🇬</b>\n\n💎 <b>{username}</b>\n\n{display_str}", parse_mode="HTML")
        except Exception:
            pass
        await asyncio.sleep(0.4)

    counts = Counter(res_symbols)
    win_amount = 0
    result_text = ""

    if counts["♥️"] >= 3 or counts["♦️"] >= 3 or counts["♠️"] >= 3 or counts["♣️"] >= 3 or counts["🀄"] >= 3:
        win_amount = random.randint(3, 60) * 1000
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

    bandit_daily_history.insert(0, bandit_record)
    if len(bandit_daily_history) > 30:
        bandit_daily_history.pop()

    final_text_str = (
        "<b>ZERO 🎰🇰🇬</b>\n\n"
        f"💎 <b>{username}</b>\n\n"
        f"{final_display}\n\n"
        f"<b>{result_text}</b>"
    )
    try:
        await msg.edit_text(final_text_str, parse_mode="HTML")
    except Exception:
        await message.answer(final_text_str, parse_mode="HTML", reply_markup=get_main_keyboard())

# --- РУЛЕТКА МЕНЮ ---
@dp.message(F.text.casefold().in_(["🎰 рулетка", "рулетка", "miniroulette"]))
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
        "<b>ZERO 🎰🇰🇬</b>\n\n"
        "🎰 <b>Минирулетка</b>\n"
        f"Монеты: {display_balance} 🪙\n"
        "Угадите число из:\n"
        "0💚\n"
        "1🔴 2⚫ 3🔴 4⚫ 5🔴 6⚫\n"
        "7🔴 8⚫ 9🔴 10⚫ 11🔴 12⚫\n\n"
        "Ставки можно текстом:\n"
        "<code>5000 2</code> | <code>5000 11</code> | <code>10000 к</code>"
    )
    await message.answer(text, reply_markup=get_roulette_inline_keyboard(), parse_mode="HTML")

# --- СТАВКИ В РУЛЕТКЕ (ИСПРАВЛЕННЫЙ РЕГЕКС ДЛЯ ПРИЕМА ЛЮБЫХ СТАВОК КАТАРЫ МЕНЕН) ---
@dp.message(F.text.casefold().regexp(r'^\d+[кк]?\s+.*$'))
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
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        return

    raw_amt_str = parts[0]
    target = parts[1].strip()

    try:
        multiplier = 1000 if "к" in raw_amt_str else 1
        clean_num = int("".join(filter(str.isdigit, raw_amt_str)))
        bet_amt = clean_num * multiplier
    except ValueError:
        return

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
        if target in ["к", "красное"] or "красн" in target:
            bet_type = "red"
            bet_desc = "на красное"
        elif target in ["ч", "черное"] or "черн" in target:
            bet_type = "black"
            bet_desc = "на черное"
        elif target in ["з", "зеленое"] or "зелен" in target:
            bet_type = 0
            bet_desc = "на зеленое"
        else:
            return

    if user_id not in ADMIN_IDS and user["balance"] < bet_amt:
        await message.answer(f"<b>ZERO 🎰🇰🇬</b>\n\n❌ <b>{username}</b>, недостаточно монет!", parse_mode="HTML")
        return

    user["pending_bets"].append({
        "amount": bet_amt,
        "type": bet_type,
        "desc": bet_desc,
        "raw_target": target
    })

    # Ставка ийгиликтүү кабыл алынды (колдонуучу катары менен каалаганча жаза алат)

# --- ЗАПУСК РУЛЕТКИ («ГО» / «КРУТИТЬ») С 3 СЕКУНДНЫМ ТАЙМЕРОМ И КАЗИНО GIF ---
@dp.message(F.text.casefold().in_(["го", "крутить"]))
async def start_game_handler(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.first_name or "Игрок"

    if user_id not in users_data or not users_data[user_id].get("pending_bets"):
        await message.answer(f"<b>ZERO 🎰🇰🇬</b>\n\n⚠️ <b>{username}</b>, сначала сделайте ставки!", parse_mode="HTML")
        return

    user_data_dict = users_data[user_id]
    bets = user_data_dict["pending_bets"]
    total_bet_amt = sum(b["amount"] for b in bets)

    if user_id not in ADMIN_IDS and user_data_dict["balance"] < total_bet_amt:
        await message.answer(f"<b>ZERO 🎰🇰🇬</b>\n\n❌ <b>{username}</b>, недостаточно монет!", parse_mode="HTML")
        user_data_dict["pending_bets"] = []
        return

    if user_id not in ADMIN_IDS:
        user_data_dict["balance"] -= total_bet_amt
    
    user_data_dict["pending_bets"] = []

    # ТАЙМЕР 3, 2, 1 СЕКУНДАН САНАП ЧЫГУУ
    timer_msg = await message.answer("<b>ZERO 🎰🇰🇬</b>\n\n🎰 Ставки приняты! До начала вращения:\n🕒 <b>3 секунды...</b>", parse_mode="HTML")
    await asyncio.sleep(1)
    await timer_msg.edit_text("<b>ZERO 🎰🇰🇬</b>\n\n🎰 Вращение рулетки:\n🕒 <b>2 секунды...</b>", parse_mode="HTML")
    await asyncio.sleep(1)
    await timer_msg.edit_text("<b>ZERO 🎰🇰🇬</b>\n\n🎰 Вращение рулетки:\n🕒 <b>1 секунда...</b>", parse_mode="HTML")
    await asyncio.sleep(1)
    
    try:
        await timer_msg.delete()
    except Exception:
        pass

    # КАЗИНО РУЛЕТКА GIF АНИМАЦИЯСЫ
    try:
        gif_msg = await message.answer_animation("https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExM3Blb3Z5b2I5aWx3MnhmODZ5bXF6a2F5dXB2NXJ0M3h6OGFqZmZ0ZSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/l0HlRnAWXxn0MhOBK/giphy.gif")
        await asyncio.sleep(3)
        await gif_msg.delete()
    except Exception:
        pass

    rolled_num = random.randint(0, 12)
    rolled_emoji = get_number_emoji(rolled_num)

    roulette_history_log.insert(0, f"{rolled_num} {rolled_emoji}")
    if len(roulette_history_log) > 10:
        roulette_history_log.pop()

    # СҮРӨТТӨГҮДӨЙ ФОРМАТ (Аты + Ставкалар катар тизмеси)
    result_lines = [
        f"<b>ZERO 🎰🇰🇬</b>\n",
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
    await message.answer(final_text, parse_mode="HTML", reply_markup=get_main_keyboard())

# --- ЛОГ ---
@dp.message(F.text.casefold() == "лог")
async def show_roulette_log(message: types.Message):
    if not roulette_history_log:
        await message.answer("<b>ZERO 🎰🇰🇬</b>\n\n📜 Лог рулетки пуст!", parse_mode="HTML")
        return
    
    log_output = "<b>ZERO 🎰🇰🇬</b>\n\n" + "\n".join(roulette_history_log)
    await message.answer(log_output, parse_mode="HTML", reply_markup=get_main_keyboard())

# --- ИСТОРИЯ ---
@dp.message(F.text.casefold().in_(["📜 история", "история"]))
async def show_bandit_history(message: types.Message):
    if not bandit_daily_history:
        await message.answer("<b>ZERO 🎰🇰🇬</b>\n\n📜 История игр за день пуст!", parse_mode="HTML")
        return

    history_output = "<b>ZERO 🎰🇰🇬</b>\n\n📜 <b>История игры «Бандит» за день:</b>\n\n" + "\n".join(bandit_daily_history)
    await message.answer(history_output, parse_mode="HTML", reply_markup=get_main_keyboard())

# --- РЕКОРД ---
@dp.message(F.text.casefold().in_(["📊 рекорд", "рекорд"]))
async def show_records(message: types.Message):
    if not users_data:
        await message.answer("<b>ZERO 🎰🇰🇬</b>\n\n📊 Рекордов пока нет!", parse_mode="HTML")
        return

    top_winner = max(users_data.items(), key=lambda x: x[1]["total_won_coins"], default=(None, {"total_won_coins": 0}))
    top_loser = max(users_data.items(), key=lambda x: x[1]["total_lost_coins"], default=(None, {"total_lost_coins": 0}))

    text = (
        "<b>ZERO 🎰🇰🇬</b>\n\n"
        "📊 <b>Автоматические рекорды игроков:</b>\n\n"
        f"🏆 <b>Топ победитель:</b> {top_winner[1]['total_won_coins']} 🪙 выиграно\n"
        f"📉 <b>Топ проигравший:</b> {top_loser[1]['total_lost_coins']} 🪙 проиграно"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_main_keyboard())

async def main():
    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
