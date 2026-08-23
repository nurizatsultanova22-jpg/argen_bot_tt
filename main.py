import asyncio
import random
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = "8620902917:AAHPuthkzK9MT7fGRWe2npjm4mY8ZwRXLWs"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Колдонуучулардын балансын убактылуу сактоо (память базасы)
user_balances = {}
user_names = {}

# '/start' баштаганда баланс белек кылуу
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    if user_id not in user_balances:
        user_balances[user_id] = 10000  # Баштапкы белек монеталар
        user_names[user_id] = user_name
        
    builder = InlineKeyboardBuilder()
    builder.button(text="🎰 Рулетка ойноо", callback_data="play_menu")
    builder.button(text="💰 Балансым", callback_data="my_balance")
    builder.adjust(1)
    
    await message.answer(
        f"🤖 Салам, **{user_name}**!\n\n"
        "Бул катардагы рулетка жана мини-оюн боту.\n"
        "Колуңуздагы виртуалдык монеталар менен ставка коюп ойноп көрүңүз!",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

# Балансты көрсөтүү
@dp.callback_query(F.data == "my_balance")
async def show_balance(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    balance = user_balances.get(user_id, 10000)
    await callback.answer(f"Сиздин балансыңыз: {balance} монет", show_alert=True)

# Оюндар менюсу
@dp.callback_query(F.data == "play_menu")
async def play_menu(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="🔴 Кызыл түскө (2x)", callback_data="bet_red")
    builder.button(text="⚫ Кара түскө (2x)", callback_data="bet_black")
    builder.adjust(1)
    
    await callback.message.edit_text(
        "🎲 **Мини-рулетка**\n\n"
        "Ставка кыла турган түсүңүздү тандаңыз:\n"
        "• Кызыл (Утсаңыз эселенип кайтат)\n"
        "• Кара (Утсаңыз эселенип кайтат)",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

# Кызыл түскө ставка (мисалы 1000 монета)
@dp.callback_query(F.data.in_({"bet_red", "bet_black"}))
async def make_bet(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    bet_amount = 1000  # Бир жолку стандарттык ставка
    
    if user_balances.get(user_id, 0) < bet_amount:
        await callback.answer("Балансыңызда монета жетишсиз!", show_alert=True)
        return
        
    # Ставканы чегебиз
    user_balances[user_id] -= bet_amount
    chosen_color = "Кызыл 🔴" if callback.data == "bet_red" else "Кара ⚫"
    
    await callback.message.edit_text(f"🎲 Ставка кабыл алынды!\nТандооңуз: {chosen_color}\nСтавка: {bet_amount} монет.\n\n⏳ Рулетка айланып жатат...")
    
    await asyncio.sleep(2)  # 2 секунд күтөбүз
    
    # Рулетканын жыйынтыгы (0 - жашыл, 1 - кызыл, 2 - кара гэсек)
    winning_result = random.choice(["Кызыл 🔴", "Кара ⚫", "Жашыл 🟢"])
    
    win_text = f"🎯 Рулетканын жыйынтыгы: **{winning_result}**\n\n"
    
    # Текшерүү
    if chosen_color == winning_result:
        win_amount = bet_amount * 2
        user_balances[user_id] += win_amount
        win_text += f"🎉 Куттуктайбыз! Сиз уттуңуз: +{win_amount} монет!"
    else:
        win_text += f"❌ Тилекке каршы, бул жолу уттурдуңуз."
        
    win_text += f"\n💳 Учурдагы балансыңыз: {user_balances[user_id]} монет."
          
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Кайра ойноо", callback_data="play_menu")
    builder.button(text="💰 Баланс", callback_data="my_balance")
    builder.adjust(2)
    
    await callback.message.edit_text(win_text, reply_markup=builder.as_markup(), parse_mode="Markdown")

async def main():
    print("Рулетка боту ишке кирди...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
