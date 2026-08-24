import asyncio
import random
import os
import re
import time
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

TOKEN = "8981337963:AAEbzzI1j3Xh34ACTb2qd3Do6bC9OKeZVYc"

bot = Bot(token=TOKEN)
dp = Dispatcher()

ADMIN_ID = 7978591176  

user_balances = {}
user_stats = {} 
current_bets = {}  # {user_id: [{"amount": ..., "color": ..., "text": ...}, ...]}
last_roulette_results = ["10⚫", "5🔴", "2⚫", "10⚫", "2⚫", "11🔴", "5🔴", "12⚫", "0🟢"]
plus_limits = {}  # {sender_id: timestamp}

# Орусча сөгүнүү сөздөрү (Антимат фильтри)
BAD_WORDS = {"сука", "бля", "блять", "хуй", "пизда", "ебать", "суки", "долбоеб", "идиот", "мразь", "уебок", "сукаа"}

def get_balance(user_id):
    if user_id == ADMIN_ID:
        return 999999999999999999  
    if user_id not in user_balances:
        user_balances[user_id] = 5000  
    return user_balances[user_id]

def get_user_stats(user_id):
    if user_id not in user_stats:
        user_stats[user_id] = {"won": 0, "lost": 0, "max_win": 0, "max_bet": 0}
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
    return builder.as_markup()

# Керексиз кнопкалар алынып салынды, минималдуу гана калтырылды
def get_main_reply_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.row(
        types.KeyboardButton(text="Рулетка"),
        types.KeyboardButton(text="Профиль")
    )
    return builder.as_markup(resize_keyboard=True)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Бот успешно запущен в максимальном качестве!", reply_markup=get_main_reply_keyboard())

# АНТИМАТ ФИЛЬТР (Орусча сөгүнгөндө жооп берүү)
@dp.message(F.text)
async def check_bad_words(message: types.Message, event_router=None):
    if not message.text:
        return
    text_lower = message.text.lower()
    words = re.findall(r'\b\w+\b', text_lower)
    for word in words:
        if word in BAD_WORDS:
            await message.reply("🚫 Орусча сөгүнүүгө болбойт!")
            return
    # Эгер сөгүнбөсө, кийинки хэндлерлерге өтөт

@dp.message(F.text.lower().in_({"профиль", "баланс"}))
async def cmd_profile(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    bal = get_balance(user_id)
    stats = get_user_stats(user_id)
    
    response = (
        f"👤 **KNK-{user_name}**\n"
        f"💳 Монеты: {bal} 🌒\n"
        f"🔥 Выиграно: {stats['won']}\n"
        f"📉 Проиграно: {stats['lost']}\n"
        f"👑 Макс. выигрыш: {stats['max_win']}"
    )
    await message.answer(response, parse_mode="Markdown")

# СТАТИСТИКА (стати / статика) - Эң көп монетасы барлар жана активдүү оюнчулар
@dp.message(F.text.lower().in_({"стати", "статика", "топ"}))
async def cmd_top_stats(message: types.Message):
    sorted_users = sorted(user_balances.items(), key=lambda item: item[1], reverse=True)[:5]
    text = "🏆 **Топ игроков по монетам (Стати):**\n\n"
    for i, (u_id, bal) in enumerate(sorted_users, 1):
        text += f"{i}. ID `{u_id}` — **{bal}** 🌒\n"
    await message.answer(text, parse_mode="Markdown")

# РЕКОРД / СТАТИСТИКА күнүмдүк эмодзилер менен
@dp.message(F.text.lower().in_({"рекорд", "рекорды"}))
async def cmd_records(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    stats = get_user_stats(user_id)
    
    text = (
        f"📊 **Игровые рекорды KNK-{user_name}** 🌒\n\n"
        f"🎉 За сегодня выиграно: **+{stats['won']}** 🥳\n"
        f"😢 За сегодня проиграно: **-{stats['lost']}** 📉\n"
        f"👑 Рекордный выигрыш: **{stats['max_win']}** ⭐\n"
        f"⚡ Максимальная ставка: **{stats['max_bet']}** 🚀"
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text.lower().in_({"рулетка", "меню"}))
async def cmd_roulette_menu(message: types.Message):
    text = (
        "🎲 **Мини-рулетка KNK**\n"
        "Угадайте число (0-12) или цвет (красное/чёрное).\n"
        "Пример ставки: `10000 на 2` же `1000 на красное`"
    )
    await message.answer(text, reply_markup=get_roulette_keyboard(), parse_mode="Markdown")

# ОТМЕТКА МЕНЕН 10000 БЕРҮҮ (Суткасына 1 гана жоил)
@dp.message(F.text.regexp(r"^[\+\+\s]*10000$"))
async def add_ten_thousand(message: types.Message):
    sender_id = message.from_user.id
    current_time = time.time()
    
    # Суткасына 1 жолу текшерүү (86400 секунд = 24 саат)
    if sender_id in plus_limits:
        last_time = plus_limits[sender_id]
        if current_time - last_time < 86400:
            hours_left = int((86400 - (current_time - last_time)) / 3600)
            await message.reply(f"❌ Вы можете давать +10000 монеталар суткасына 1 гана жолу! Подождите још {hours_left} ч.")
            return

    target_user_id = None
    target_name = ""

    if message.reply_to_message and message.reply_to_message.from_user:
        target_user_id = message.reply_to_message.from_user.id
        target_name = message.reply_to_message.from_user.first_name
    elif message.entities:
        for entity in message.entities:
            if entity.type == "text_mention":
                target_user_id = entity.user.id
                target_name = entity.user.first_name

    if target_user_id:
        plus_limits[sender_id] = current_time
        if target_user_id not in user_balances:
            user_balances[target_user_id] = 5000
        user_balances[target_user_id] += 10000
        await message.answer(f"✅ Успешно! Пользователю KNK-{target_name} добавлено +10000 🌒\n💳 Новый баланс: {user_balances[target_user_id]} 🌒")

# СТАВКАЛАРДЫ КАТТОО (Бир адам бир нече ставка кошо алат)
@dp.message(F.text.regexp(r"^(\d+)\s*([кч]|\d+|на\s*красное|на\s*чёрное|красное|чёрное|к|ч)$", flags=re.IGNORECASE))
async def parse_bet(message: types.Message):
    text = message.text.strip()
    match = re.match(r"^(\d+)\s*(.*)$", text, re.IGNORECASE)
    if not match:
        return
        
    amount = int(match.group(1))
    target = match.group(2).lower().strip()
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    bal = get_balance(user_id)
    if bal < amount and user_id != ADMIN_ID:
        await message.answer(f"KNK-{user_name}, недостаточно монет ❌")
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
    else:
        return
        
    # Колдонуучунун ставкаларын тизмеге кошуу (өчүрүлүп кетпейт)
    if user_id not in current_bets:
        current_bets[user_id] = []
        
    current_bets[user_id].append({"amount": amount, "color": color, "text": color_text})
    
    stats = get_user_stats(user_id)
    if amount > stats['max_bet']:
        stats['max_bet'] = amount

    if user_id != ADMIN_ID:
        user_balances[user_id] -= amount
    
    await message.answer(f"Ставка принята: KNK-{user_name} {amount} монет {color_text}")

# «ГО» ДЕГЕНДЕ БАРДЫК СТАВКАЛАР ОЙНОЛОТ
@dp.message(F.text.lower().in_({"го", "рулетка крутит", "крутить"}))
async def spin_roulette(message: types.Message):
    if not current_bets:
        await message.answer("⚠️ Ни у кого нет активных ставок! Сначала сделайте ставки.")
        return
        
    msg = await message.answer(f"🎰 Крутим рулетку...")
    await asyncio.sleep(2.0)
    try:
        await msg.delete()
    except:
        pass

    # Жакшыртылган сапаттуу рулетка GIF анимациясы
    gif_url = "https://media.giphy.com/media/xT5LMRQ628iuRMVMwo/giphy.gif"
    gif_msg = None
    try:
        gif_msg = await message.answer_animation(animation=gif_url)
    except:
        gif_msg = await message.answer("🎲 [Рулетка вращается...]")

    await asyncio.sleep(3.0)

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
    response = f"🎰 Рулетка: {winning_result}\n\n"

    active_bets_copy = current_bets.copy()
    current_bets.clear()

    for u_id, bets_list in active_bets_copy.items():
        # Колдонуучунун атын биринчи ставкасынан алабыз
        u_name = "Игрок"
        stats = get_user_stats(u_id)
        
        for bet in bets_list:
            is_win = False
            if str(bet["color"]) == str(winning_number):
                is_win = True
                win_multiplier = 12 if winning_number != 0 else 14
                win_amount = bet["amount"] * win_multiplier
            elif bet["color"] == win_color:
                is_win = True
                win_amount = bet["amount"] * 2
            else:
                win_amount = 0

            if is_win:
                if u_id != ADMIN_ID:
                    if u_id not in user_balances:
                        user_balances[u_id] = 5000
                    user_balances[u_id] += win_amount
                stats['won'] += win_amount
                if win_amount > stats['max_win']:
                    stats['max_win'] = win_amount
                response += f"🎉 KNK-{u_id} выиграл {win_amount} на {bet['text']}\n"
            else:
                stats['lost'] += bet["amount"]
                response += f"❌ KNK-{u_id} проиграл {bet['amount']} на {bet['text']}\n"
        
        current_bal = get_balance(u_id)
        response += f"💳 Баланс: {current_bal} 🌒\n------------------\n"
    
    await message.answer(response)

@dp.callback_query()
async def callback_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_name = callback.from_user.first_name
    data = callback.data
    
    if data == "bet_red_1k":
        bal = get_balance(user_id)
        if bal < 1000 and user_id != ADMIN_ID:
            await callback.answer("Недостаточно монет!", show_alert=True)
            return
        if user_id not in current_bets:
            current_bets[user_id] = []
        current_bets[user_id].append({"amount": 1000, "color": "красное", "text": "на красное"})
        if user_id != ADMIN_ID:
            user_balances[user_id] -= 1000
        await callback.message.answer(f"Ставка принята: KNK-{user_name} 1000 монет на красное")
    elif data == "bet_black_1k":
        bal = get_balance(user_id)
        if bal < 1000 and user_id != ADMIN_ID:
            await callback.answer("Недостаточно монет!", show_alert=True)
            return
        if user_id not in current_bets:
            current_bets[user_id] = []
        current_bets[user_id].append({"amount": 1000, "color": "чёрное", "text": "на чёрное"})
        if user_id != ADMIN_ID:
            user_balances[user_id] -= 1000
        await callback.message.answer(f"Ставка принята: KNK-{user_name} 1000 монет на чёрное")
    elif data == "bet_green_1k":
        bal = get_balance(user_id)
        if bal < 1000 and user_id != ADMIN_ID:
            await callback.answer("Недостаточно монет!", show_alert=True)
            return
        if user_id not in current_bets:
            current_bets[user_id] = []
        current_bets[user_id].append({"amount": 1000, "color": "зелёный", "text": "на зелёный"})
        if user_id != ADMIN_ID:
            user_balances[user_id] -= 1000
        await callback.message.answer(f"Ставка принята: KNK-{user_name} 1000 монет на зелёный")
    elif data == "action_spin":
        fake_msg = callback.message
        fake_msg.from_user = callback.from_user
        await spin_roulette(fake_msg)
    await callback.answer()

async def main():
    print("Bot started in maximum quality!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
