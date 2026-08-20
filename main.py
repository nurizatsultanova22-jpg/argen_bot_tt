import os
import threading
import random
import asyncio
from flask import Flask
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

TELEGRAM_TOKEN = "8943857517:AAHKx8raz2WrxYeHI2hjE1f5TpnygJq2vZE"

# ӨЗҮҢДҮН TELEGRAM IDИҢДИ БУЛ ЖЕРГЕ ЖАЗ (сан түрүндө)
ADMIN_ID = 123456789  # <--- Өз IDңди жаз!

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# Колдонуучулардын маалыматтары (Баланс, аты ж.б.)
users_data = {}

# Админ донат кошуу үчүн FSM абалдары
class AdminTopUp(StatesGroup):
    waiting_for_amount = State()

# Flask веб сервер (Render үчүн)
app_web = Flask(__name__)
@app_web.route('/')
def home():
    return "Mini-Roulette & Donat Bot is active!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host="0.0.0.0", port=port)

# Дизайн кнопкалары
RED = "🔴"
BLACK = "🖤"
GREEN = "💚"

WHEEL = {
    0: GREEN, 1: RED, 2: BLACK, 3: RED, 4: BLACK, 5: RED,
    6: BLACK, 7: RED, 8: BLACK, 9: RED, 10: BLACK, 11: RED, 12: BLACK
}

def get_menu_kb():
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="1 - 3", callback_data="bet_range_1_3"),
        types.InlineKeyboardButton(text="4 - 6", callback_data="bet_range_4_6"),
        types.InlineKeyboardButton(text="7 - 9", callback_data="bet_range_7_9"),
        types.InlineKeyboardButton(text="10 - 12", callback_data="bet_range_10_12")
    )
    builder.row(
        types.InlineKeyboardButton(text="1k на 🔴", callback_data="bet_red_1000"),
        types.InlineKeyboardButton(text="1k на 🖤", callback_data="bet_black_1000"),
        types.InlineKeyboardButton(text="1k на 0💚", callback_data="bet_zero_1000")
    )
    builder.row(
        types.InlineKeyboardButton(text="Повторить", callback_data="repeat"),
        types.InlineKeyboardButton(text="Удвоить", callback_data="double"),
        types.InlineKeyboardButton(text="Крутить", callback_data="spin")
    )
    # Донат баскычы (Сиздин юзернеймге багыттайт)
    builder.row(
        types.InlineKeyboardButton(text="💎 Донат", url="https://t.me/Argen_70")
    )
    return builder.as_markup()

def get_user(user_id, name="Игрок"):
    if user_id not in users_data:
        users_data[user_id] = {
            "name": name,
            "balance": 5000,  # Баштапкы баланс 5000
            "last_bet": ("red", 1000),
            "history": []
        }
    return users_data[user_id]

@dp.message(Command("start"))
async def start(message: types.Message):
    user = message.from_user
    user_data = get_user(user.id, user.first_name)
    bal = user_data["balance"]
    
    text = (
        f"🎰 *Минирулетка*\n"
        f"Баланс: {bal} 🌕\n\n"
        f"Угадайте число из:\n"
        f"0{GREEN}\n"
        f"1{RED} 2{BLACK} 3{RED} 4{BLACK} 5{RED} 6{BLACK}\n"
        f"7{RED} 8{BLACK} 9{RED} 10{BLACK} 11{RED} 12{BLACK}\n\n"
        f"Ставки можно текстом:\n"
        f"`1000 на красное` | `5000 на 12`\n\n"
        f"💡 Ваш ID болуу үчүн /id командасын басыңыз."
    )
    await message.answer(text, reply_markup=get_menu_kb(), parse_mode="Markdown")

@dp.message(F.text.lower() == "рулетка")
async def start_roulette_word(message: types.Message):
    await start(message)

# ==========================================
# КОЛДОНУУЧУ ҮЧҮН /ID КОМАНДАСЫ
# ==========================================
@dp.message(Command("id"))
async def get_my_id(message: types.Message):
    user_id = message.from_user.id
    await message.answer(f"Ваш Telegram ID: `{user_id}`", parse_mode="Markdown")

# ==========================================
# АДМИН ҮЧҮН БАЛАНС ТОЛУКТОО ЛОГИКАСЫ
# ==========================================

# 1. Админ каалаган колдонуучунун ID сизин жазат (мисалы: 12345678)
@dp.message(F.text.regexp(r"^\d+$"))
async def admin_check_user_id(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return  # Эгер админ болбосо үн катпайт

    target_id = int(message.text)
    
    # Эгер бот бул юзерди билбесе, базага кошуп коёбуз
    if target_id not in users_data:
        users_data[target_id] = {"name": "Игрок", "balance": 5000, "last_bet": ("red", 1000), "history": []}

    # Состояниеге ID сактап, сумма сурайбыз
    await state.update_data(target_id=target_id)
    await message.answer(f"Пользователь с ID `{target_id}` найден.\nТекущий баланс: {users_data[target_id]['balance']} 🌕\n\nВведите сумму для пополнения:", parse_mode="Markdown")
    await state.set_state(AdminTopUp.waiting_for_amount)

# 2. Админ сумманы жазат
@dp.message(AdminTopUp.waiting_for_amount)
async def admin_set_amount(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    if not message.text.isdigit():
        await message.answer("❌ Пожалуйста, введите корректное число!")
        return

    amount = int(message.text)
    data = await state.get_data()
    target_id = data.get("target_id")

    # Баланска кошуу
    users_data[target_id]["balance"] += amount
    new_bal = users_data[target_id]["balance"]

    await message.answer(f"✅ Успешно! Игроку (ID: `{target_id}`) добавлено {amount} 🌕.\nНовый баланс: {new_bal} 🌕", parse_mode="Markdown")
    
    # Колдонуучуга да кабар жиберүү
    try:
        await bot.send_message(target_id, f"🎉 Ваш баланс пополнен на {amount} 🌕!\nБаланс: {new_bal} 🌕")
    except Exception:
        pass

    await state.clear()

# ==========================================
# РУЛЕТКА ЖАНА СТАВКАЛАР
# ==========================================

@dp.message(F.text.regexp(r"(\d+)\s+на\s+(красное|черное|зеленое|\d+)"))
async def make_bet(message: types.Message):
    await message.reply("Ставка принята 🎲")

# "Го" же "Крутить" деп жазганда рулетка айлануусу
@dp.message(F.text.lower().in_(["го", "крутить"]))
async def spin_roulette_text(message: types.Message):
    await execute_spin(message)

async def execute_spin(message_or_callback):
    is_callback = isinstance(message_or_callback, types.CallbackQuery)
    message = message_or_callback.message if is_callback else message_or_callback
    user_id = message_or_callback.from_user.id
    
    user_data = get_user(user_id, message_or_callback.from_user.first_name)
    
    msg = await message.answer("⬜⬜⬜⬜⬜")
    await asyncio.sleep(0.5)
    
    winning_number = random.randint(0, 12)
    color_emoji = WHEEL[winning_number]
    
    result_text = f"Рулетка: {winning_number}{color_emoji}"
    await msg.edit_text(result_text)

@dp.callback_query(F.data == "spin")
async def callback_spin(callback: types.CallbackQuery):
    await callback.answer()
    await execute_spin(callback)

@dp.callback_query(F.data.startswith("bet_"))
async def callback_bet(callback: types.CallbackQuery):
    await callback.answer("Ставка принята 🎲")

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    dp.run_polling(bot)
