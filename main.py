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
current_bets = {}  
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
        types.InlineKeyboardButton(text="Повторить", callback_data="action_repeat"),
        types.InlineKeyboardButton(text="Удвоить", callback_data="action_double"),
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

@dp.message(F.text.lower().in_({"б", "баланс"}))
async def cmd_balance_simple(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    bal = get_balance(user_id)
    
    response = f"ZERO-{user_name}\nмонеты: {bal} 🌒"
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🎁 Ежедневные награды (Pass)", callback_data="daily_pass_menu"))
    
    await message.answer(response, reply_markup=builder.as_markup())

@dp.message(F.text.lower().in_({"профиль", "📋профиль"}))
async def cmd_profile(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    bal = get_balance(user_id)
    stats = get_user_stats(user_id)
    stats['name'] = user_name
    
    response = (
        f"👤 **Профиль игрока ZERO-{user_name}**\n\n"
        f"💳 Баланс: **{bal}** 🌒\n"
        f"🎮 Сыграно игр: {stats['games_played']}\n"
        f"🔥 Всего выиграно: **+{stats['won']}** 🌒\n"
        f"📉 Всего проиграно: **-{stats['lost']}** 🌒\n"
        f"👑 Максимальный выигрыш: **{stats['max_win']}** 🌒\n"
        f"⚡ Максимальная ставка: **{stats['max_bet']}** 🌒"
    )
    await message.answer(response, parse_mode="Markdown")

@dp.message(F.text.lower().in_({"стати", "статистика", "рекорд", "рекорды", "топ"}))
async def cmd_stats_top(message: types.Message):
    if not user_stats:
        await message.answer("📊 Пока нет данных об игроках для формирования рекордов.")
        return

    sorted_by_win = sorted(user_stats.items(), key=lambda x: x[1]['won'], reverse=True)[:3]
    sorted_by_loss = sorted(user_stats.items(), key=lambda x: x[1]['lost'], reverse=True)[:1]

    medals = ["🥇", "🥈", "🥉"]
    top_win_text = ""
    for i, (u_id, st) in enumerate(sorted_by_win):
        medal = medals[i] if i < len(medals) else "▫️"
        name = st.get('name', f"ID {u_id}")
        top_win_text += f"{medal} **{name}** — {st['won']} монет (рекорд выигрыша)\n"

    if not top_win_text:
        top_win_text = "Пока нет данных\n"

    loss_text = "Пока нет данных"
    if sorted_by_loss:
        u_id, st = sorted_by_loss[0]
        name = st.get('name', f"ID {u_id}")
        loss_text = f"🥇 **{name}** — {st['lost']} монет (рекорд проигрыша)"

    top_thief = sorted(user_stats.items(), key=lambda x: x[1]['max_bet'], reverse=True)
    thief_text = "Пока нет данных"
    if top_thief:
        u_id, st = top_thief[0]
        name = st.get('name', f"ID {u_id}")
        thief_text = f"🥇 **{name}** (`{u_id}`) — {st['max_bet']} монет"

    text = (
        f"💰 **Глобальный рекорд дня (топ 3) — ZERO**\n"
        f"────────────────────────\n"
        f"{top_win_text}"
        f"🥉 {loss_text}\n"
        f"────────────────────────\n"
        f"🥷 **Вор в законе дня**\n"
        f"{thief_text}\n"
        f"_Сброс: каждый день в 00:00 (Москва)_\n"
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text.lower().in_({"лог", "логи"}))
async def cmd_logs(message: types.Message):
    logs_text = "\n".join(last_roulette_results[-12:])
    await message.answer(logs_text)

@dp.message(F.text.lower().in_({"рулетка", "меню"}))
async def cmd_roulette_menu(message: types.Message):
    text = (
        "Минирулетка ZERO\n"
        "Угадайте число из:\n"
        "0🟢 | 1🔴 2⚫ 3🔴 4⚫ 5🔴 6⚫\n"
        "Ставки текстом: `1000 на красное` же `5000 на 12`"
    )
    await message.answer(text, reply_markup=get_roulette_keyboard())

@dp.message(F.text.lower().in_({"📖помощь", "помощь", "/help"}))
async def cmd_help(message: types.Message):
    help_text = "📖 Справка ZERO: жазыңыз 'открыть', 'рулетка', 'профиль', 'рекорд' же ставка жасаңыз."
    await message.answer(help_text)

@dp.message(F.text.lower().in_({"💳 донат", "донат"}))
async def cmd_donate_text(message: types.Message):
    donate_text = (
        "Монеты ZERO 🪙\n"
        "200.000 - 100₽\n"
        "500.000 - 230₽\n"
        "1.000.000 - 450₽\n"
        "Суроолор боюнча: @Argen_70"
    )
    await message.answer(donate_text)

@dp.message(F.text.regexp(r"^[\+\+\s]*(\d+)$"))
async def add_money_by_reply_or_mention(message: types.Message):
    match = re.match(r"^[\+\+\s]*(\d+)$", message.text.strip())
    if not match:
        return
    amount = int(match.group(1))
    sender_id = message.from_user.id
    sender_name = message.from_user.first_name
    
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
        if target_user_id == sender_id:
            await message.answer("❌ Өзүңүзгө монета которо албайсыз!")
            return

        if sender_id != ADMIN_ID:
            current_time = time.time()
            if sender_id in give_money_limits:
                if current_time - give_money_limits[sender_id] < 86400:
                    await message.answer("❌ Лимит! Суткасына 1 жолу гана монета бере аласыз.")
                    return
            sender_bal = get_balance(sender_id)
            if sender_bal < amount:
                await message.answer(f"❌ Балансыңызда монета жетишсиз ({amount}). Баланс: {sender_bal}")
                return
            user_balances[sender_id] -= amount
            give_money_limits[sender_id] = current_time

        if target_user_id not in user_balances:
            user_balances[target_user_id] = 5000
        user_balances[target_user_id] += amount
        
        await message.answer(f"✅ Ийгиликтүү! ZERO-{target_name} +{amount} 🌒 алды.")

@dp.message(F.text.lower().in_({"бандит", "слот", "однорукий бандит"}))
async def play_bandit(message: types.Message):
    global game_counter
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    bal = get_balance(user_id)
    bet_amount = 500
    
    if bal < bet_amount and user_id != ADMIN_ID:
        await message.answer(f"ZERO-{user_name}, монета жетишсиз ❌")
        return
        
    if user_id != ADMIN_ID:
        user_balances[user_id] -= bet_amount

    stats = get_user_stats(user_id)
    stats['name'] = user_name
    stats['games_played'] += 1
    if bet_amount > stats['max_bet']:
        stats['max_bet'] = bet_amount

    dice_msg = await message.answer_dice(emoji="🎰")
    await asyncio.sleep(3.5)
    val = dice_msg.dice.value
    
    win_amount = 70000 if val == 64 else (random.choice([10000, 20000]) if val in [22, 43] else 0)

    if win_amount > 0:
        if user_id == ADMIN_ID:
            user_balances[ADMIN_ID] += win_amount
        else:
            if user_id not in user_balances:
                user_balances[user_id] = 5000
            user_balances[user_id] += win_amount
        stats['won'] += win_amount
        if win_amount > stats['max_win']:
            stats['max_win'] = win_amount
        await message.answer(f"🎉 Бандиттен уттуңуз: +{win_amount} 🌒")
    else:
        stats['lost'] += bet_amount
        await message.answer(f"❌ Утулуп калдыңыз: -{bet_amount} 🌒")

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
            await callback.answer("❌ Вы уже забирали награду сегодня! Приходите через 24 часа.", show_alert=True)
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
        
        await callback.answer(f"🎉 Кундук сыйлык берилди: +{reward_amount} 🌒", show_alert=True)
        await show_pass_menu(callback, is_callback=True)
        return

    elif data == "back_to_main":
        try:
            await callback.message.edit_text("Главное меню ZERO. Выберите действие:", reply_markup=get_roulette_keyboard())
        except:
            await callback.message.answer("Главное меню ZERO. Выберите действие:", reply_markup=get_roulette_keyboard())
        await callback.answer()
        return

    elif data == "open_roulette":
        await cmd_roulette_menu(callback.message)
        await callback.answer()
        return

    await callback.answer()

async def main():
    # Бот күйгөндө профилге көк «Открыть» баскычын орнотуу (Web App аркылуу)
    # Эскертүү: link катары өзүңүздүн сайтындын же мини-апптын ссылкасын коёсуз (мисалы t.me боттун webapp же hosted сайты)
    try:
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="Открыть",
                web_app=WebAppInfo(url="https://t.me/RoyalDnoBot") # Өзүңүздүн боттун ссылкасын же мини-апп дарегин жазсаңыз болот
            )
        )
    except Exception as e:
        print(f"Menu button set error: {e}")

    print("Bot ZERO started successfully with Profile Menu Button!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
