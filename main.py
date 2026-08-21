import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = "8814386262:AAE8LnwkKaQMVSb96GE_N6VLmQ3Q5RVj2FM"
CHANNEL_LINK = "https://t.me/taanyshuu_chatyy"

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

class AnonymousStates(StatesGroup):
    waiting_for_message = State()

def get_main_menu(my_user_id):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Менин шилтемемди алуу", callback_data=f"get_link_{my_user_id}"),
        InlineKeyboardButton(text="Таанышуу чат", url=CHANNEL_LINK),
    )
    return builder.as_markup()

@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    args = message.text.split()
    if len(args) > 1:
        target_id = args[1]
        await state.update_data(target_id=target_id)
        await message.answer("Бул адамга жашыруун кат жаз. Ким экениңди билишпейт!")
        await message.answer("Билдирүүнү жазыңыз:")
        await state.set_state(AnonymousStates.waiting_for_message)
    else:
        bot_info = await bot.get_me()
        my_link = f"https://t.me/{bot_info.username}?start={message.from_user.id}"
        await message.answer(f"Салам! Досторуңа жөнөтүү үчүн шилтемең: {my_link}", reply_markup=get_main_menu(message.from_user.id))

@dp.message(AnonymousStates.waiting_for_message)
async def handle_message(message: types.Message, state: FSMContext):
    data = await state.get_data()
    target_id = data.get("target_id")
    if target_id:
        try:
            await bot.send_message(int(target_id), f"Жаңы анонимдүү билдирүү: {message.text}")
            await message.answer("Кат жөнөтүлдү!")
        except:
            await message.answer("Кат жетпей калды.")
    await state.clear()

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
