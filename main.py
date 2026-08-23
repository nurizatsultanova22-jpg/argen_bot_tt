import asyncio
import random
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = "8620902917:AAHPuthkzK9MT7fGRWe2npjm4mY8ZwRXLWs"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Колдонуучулардын балансы жана логдору
user_balances = {}
user_names = {}

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    if user_id not in user_balances:
        user_balances[user_id] = 124000  # Баштапкы монеталар
        user_names[user_id] = user_name
        
    builder = InlineKeyboardBuilder()
    builder.button(text="🎰 Рулетка ойноо", callback_data="play_menu")
    builder.button(text="💰 Баланс", callback_data="my_balance")
    builder.adjust(1)
    
    await message.answer(
        f"🤖 Салам, **{user_name}**!\n\n"
        "Сиз каалаган рулетка жана ставка оюну даяр.\n"
        "Монеталарыңыз менен кара же кызыл түскө ставка коюп ойноңуз!",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "my_balance")
async def show_balance(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    balance = user_balances.get(user_id, 124000)
    await callback.answer(f"💳 Монеталар: {balance}", show_alert=True)

@dp.callback_query(F.data == "play_menu")
async def play_menu(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="🔴 Кызылга 30000 к", callback_data="bet_red_30000")
    builder.button(text="⚫ Карага 30000 к", callback_data="bet_black_30000")
    builder.button(text="💰 Баланс", callback_data="my_balance")
    builder.adjust(1)
    
    await callback.message.edit_text(
        "🎲 **Рулетка менюсу**\n\n"
        "Түстү жана ставкаңызды тандаңыз:\n"
        "• 🔴 Кызыл (30000 монета)\n"
        "• ⚫ Кара (30000 монета)",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.in_({"bet_red_30000", "bet_black_30000"}))
async def make_bet(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_name = user_names.get(user_id, "Оюнчу")
    bet_amount = 30000
    
    if user_balances.get(user_id, 0) < bet_amount:
        await callback.answer("❌ Балансыңызда монета жетишсиз!", show_alert=True)
        return
        
    # Баланстан чегебиз
    user_balances[user_id] -= bet_amount
    
    is_red = "red" in callback.data
    color_name = "кызылга (к)" if is_red else "карага (к)"
    chosen_color_text = "Кызыл 🔴" if is_red else "Кара ⚫"
    
    # Видеодогудай лог жарыялайбыз
    log_text = (
        f"👑 **RDNO**\n"
        f"Ставка принята: ✈️ **{user_name}** 30000 монета на {color_name}\n\n"
        f"⏳ Рулетка айланып жатат (10 сек)..."
    )
    await callback.message.edit_text(log_text, parse_mode="Markdown")
    
    # 2 секунд күтөбүз (рулетка айлануу имитациясы)
    await asyncio.sleep(2)
    
    # Рулетканын жыйынтыгын чыгарабыз (Кызыл же Кара)
    winning_result = random.choice(["Кызыл 🔴", "Кара ⚫"])
    
    result_msg = f"🎰 **Рулетка: {winning_result}**\n\n"
    result_msg += f"👤 {user_name} тандаганы: {chosen_color_text}\n"
    
    if (is_red and winning_result == "Кызыл 🔴") or (not is_red and winning_result == "Кара ⚫"):
        win_amount = bet_amount * 2
        user_balances[user_id] += win_amount
        result_msg += f"🎉 **Выиграл {win_amount} на {color_name}г!**\n"
    else:
        result_msg += f"❌ **Проиграл 30000 на {color_name}г.**\n"
        
    result_msg += f"\n💰 Монеты: {user_balances[user_id]}"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Кайра ойноо", callback_data="play_menu")
    builder.button(text="💳 Баланс", callback_data="my_balance")
    builder.adjust(2)
    
    await callback.message.edit_text(result_msg, reply_markup=builder.as_markup(), parse_mode="Markdown")

async def handle(request):
    return web.Response(text="Bot is running!")

async def web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

async def main():
    await web_server()
    print("Рулетка боту ишке кирди...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
