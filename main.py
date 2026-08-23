import asyncio
import random
import re
import time
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

TOKEN = "8620902917:AAHPuthkzK9MT7fGRWe2npjm4mY8ZwRXLWs"

bot = Bot(token=TOKEN)
dp = Dispatcher()

ADMIN_ID = 7978591176  

user_balances = {}
user_stats = {} 
current_bets = {}
last_roulette_results = ["10⚫", "5🔴", "2⚫", "10⚫", "2⚫", "11🔴", "5🔴", "12⚫", "0🟢"]

def get_balance(user_id):
    if user_id == ADMIN_ID:
        return 999999999999999999  
    if user_id not in user_balances:
        user_balances[user_id] = 5000  
    return user_balances[user_id]

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="Главное меню"), types.KeyboardButton(text="Рулетка"))
    builder.row(types.KeyboardButton(text="Бандит"), types.KeyboardButton(text="💳 Донат"))
    await message.answer("Салам! Бот иштеп жатат.", reply_markup=builder.as_markup(resize_keyboard=True))

@dp.message(F.text.lower().in_({"б", "баланс"}))
async def cmd_balance_simple(message: types.Message):
    user_id = message.from_user.id
    bal = get_balance(user_id)
    await message.answer(f"Монеты: {bal} 🌕")

@dp.message(F.text.lower().in_({"рулетка", "главное меню"}))
async def cmd_roulette_menu(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="1к на 🔴", callback_data="bet_red_1k"),
        types.InlineKeyboardButton(text="1к на ⚫", callback_data="bet_black_1k"),
        types.InlineKeyboardButton(text="Крутить", callback_data="action_spin")
    )
    await message.answer("Рулетка менюсу:", reply_markup=builder.as_markup())

@dp.callback_query()
async def callback_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_name = callback.from_user.first_name
    data = callback.data
    
    if data == "bet_red_1k":
        current_bets[user_id] = {"amount": 1000, "color": "красное"}
        await callback.message.answer(f"Ставка принята: 1000 на красное")
    elif data == "bet_black_1k":
        current_bets[user_id] = {"amount": 1000, "color": "чёрное"}
        await callback.message.answer(f"Ставка принята: 1000 на чёрное")
    elif data == "action_spin":
        if user_id not in current_bets:
            await callback.answer("Сначала сделайте ставку!", show_alert=True)
            return
        winning_number = random.randint(0, 12)
        win_color = "красное" if winning_number % 2 != 0 else "чёрное"
        bet = current_bets[user_id]
        
        response = f"Рулетка: {winning_number}\n"
        if bet["color"] == win_color:
            response += "🎉 Вы выиграли 2000 монет!"
        else:
            response += "❌ Вы проиграли."
        del current_bets[user_id]
        await callback.message.answer(response)
    await callback.answer()

async def main():
    print("Bot started successfully!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
