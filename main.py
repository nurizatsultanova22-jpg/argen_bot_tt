import asyncio
import logging
import random
from datetime import datetime
from aiogram import Bot, Dispatcher, F, types

TOKEN = "8981337963:AAG0tCPAwXo1ldR20VMLODwKPKnsBqgdi4Q"

bot = Bot(token=TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

# Өзүңүздүн Telegram ID'ңизди ушул жерге жазыңыз (админ үчүн)
ADMIN_IDS = {123456789}  # <-- Өзүңүздүн ID менен алмаштырыңыз!

# Бардык оюнчулардын маалыматтары жана рекорддор
users_data = {}
all_wins_records = []   
all_loses_records = []  

# Күнүмдүк которууларды текшерүү үчүн словарь
daily_transfer_limits = {}

# --- БАНДИТ (СЛОТ) ОЮНУ ЖАНА ТАК ШАРТТАР ---
@dp.message(F.text.lower().in_(["бандит", "слот", "bandit"]))
async def cmd_bandit(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.first_name or "Игрок"
    
    if user_id not in users_data:
        users_data[user_id] = {
            "balance": 507000,
            "bandit_history": [],
            "total_won_coins": 0,
            "total_lost_coins": 0
        }
    
    user = users_data[user_id]
    cost = 1000  # Бир жолку ойноо баасы

    if user["balance"] < cost:
        await message.answer("❌ Балансыңызда бандит ойноо үчүн монета жетишсиз! (Керек: 1000 🪙)")
        return

    user["balance"] -= cost

    symbols = ["♥️", "♦️", "♠️", "🎴", "🀄"]
    slot1 = random.choice(symbols)
    slot2 = random.choice(symbols)
    slot3 = random.choice(symbols)
    slot4 = random.choice(symbols)

    # 4 торчолуу төрт бурчтуу стилдеги көрүнүш
    slot_board = (
        f"🎰 <b>БАНДИТ ОЮНУ</b> 🎰\n\n"
        f" ┌─────────┐\n"
        f" │ {slot1} │ {slot2} │\n"
        f" ├─────────┤\n"
        f" │ {slot3} │ {slot4} │\n"
        f" └─────────┘\n\n"
    )

    all_symbols = [slot1, slot2, slot3, slot4]
    win_amount = 0
    win_desc = ""

    # Сиз талап кылган так утуш шарттары
    if all_symbols.count("🎴") == 4:
        win_amount = 70000
        win_desc = "🔥 4x 🎴 чыкты! Утуш: 70,000 монет!"
    elif all_symbols.count("♥️") == 4:
        win_amount = 15000
        win_desc = "💖 4x Жүрөк (♥️) чыкты! Утуш: 15,000 монет!"
    elif all_symbols.count("🀄") >= 3:
        win_amount = 10000
        win_desc = "🀄 3x 🀄 чыкты! Утуш: 10,000 монет!"
    elif all_symbols.count("♦️") >= 3:
        win_amount = 6000
        win_desc = "♦️ 3x Бриллиант чыкты! Утуш: 6,000 монет!"
    elif all_symbols.count("♥️") >= 3:
        win_amount = 3000
        win_desc = "♥️ 3x Жүрөк чыкты! Утуш: 3,000 монет!"
    elif all_symbols.count("♠️") >= 3:
        win_amount = 3000
        win_desc = "♠️ 3x Пика чыкты! Утуш: 3,000 монет!"

    current_time = datetime.now().strftime("%H:%M:%S")

    if win_amount > 0:
        user["balance"] += win_amount
        user["total_won_coins"] += win_amount
        all_wins_records.append({"name": username, "amount": win_amount})
        
        user["bandit_history"].append(f"[{current_time}] Утуш: +{win_amount} 🪙 ({slot1} {slot2} {slot3} {slot4})")
        result_text = f"{slot_board}🎉 <b>{username}</b>, куттуктайбыз! {win_desc}\n💰 Баланс: {user['balance']} 🪙︎"
    else:
        user["total_lost_coins"] += cost
        all_loses_records.append({"name": username, "amount": cost})
        
        user["bandit_history"].append(f"[{current_time}] Утулуу: -{cost} 🪙 ({slot1} {slot2} {slot3} {slot4})")
        result_text = f"{slot_board}❌ <b>{username}</b>, бул жолу утулган жоксуз (-1000 🪙).\n💰 Баланс: {user['balance']} 🪙︎"

    if len(user["bandit_history"]) > 15:
        user["bandit_history"].pop(0)

    await message.answer(result_text, parse_mode="HTML")

# --- "ИСТОРИЯ" КОМАНДАСЫ ---
@dp.message(F.text.lower().in_(["история", "history"]))
async def show_bandit_history(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.first_name or "Игрок"

    if user_id not in users_data or not users_data[user_id].get("bandit_history"):
        await message.answer(f"📜 <b>{username}</b>, сиз азырынча бандит оюнун ойногон жоксуз же тарыхыңыз бош.")
        return

    user = users_data[user_id]
    history_lines = "\n".join(user["bandit_history"])
    
    summary_text = (
        f"📊 <b>{username} - Бандит оюнунун тарыхы</b>\n\n"
        f"📈 Бардык уткан монеталарыңыз: <b>+{user['total_won_coins']} 🪙</b>\n"
        f"📉 Бардык уттурган монеталарыңыз: <b>-{user['total_lost_coins']} 🪙</b>\n\n"
        f"<b>Акыркы оюндарыңыз:</b>\n"
        f"{history_lines}"
    )
    await message.answer(summary_text, parse_mode="HTML")

# Админ закреп кылуу (билдирүүгө жооп кайтарып "закреп" деп жазуу)
@dp.message(F.reply_to_message, F.text.lower() == "закреп")
async def pin_message_admin(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    try:
        await message.reply_to_message.pin()
        await message.answer("📌 Билдирүү ийгиликтүү закреп кылынды!")
    except Exception as e:
        await message.answer(f"❌ Ката кетти (Ботто админ укугу бар экенин текшериңиз): {e}")

# Антиспам жана шилтемелерди өчүрүү
@dp.message(F.text | F.caption)
async def anti_spam_and_ads(message: types.Message):
    text = message.text or message.caption or ""
    text_lower = text.lower()

    if text_lower in ["закреп", "история", "history", "бандит", "слот", "bandit"]:
        return

    is_link_or_ad = any(sub in text_lower for sub in ["t.me/", "https://", "http://", "www.", "telegram.me"])

    if is_link_or_ad:
        if message.from_user.id in ADMIN_IDS:
            await message.answer("📢 <b>Админ тарабынан маалымат:</b>", parse_mode="HTML")
            return
        else:
            try:
                await message.delete()
            except:
                pass
            
            warning_msg = await message.answer(f"❌ <b>{message.from_user.first_name or 'Колдонуучу'}</b>, чатка шилтеме же жарнама жөнөтүүгө болбойт!")
            await asyncio.sleep(5)
            try:
                await warning_msg.delete()
            except:
                pass
            return

# "/id" командасы
@dp.message(F.text.lower() == "/id")
async def show_user_id(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.first_name or "Колдонуучу"
    await message.answer(f"👤 <b>{username}</b>, сенин ID номериң:\n🆔 <code>{user_id}</code>", parse_mode="HTML")

# Балансты көрүү ("б")
@dp.message(F.text.lower() == "б")
async def show_balance(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.first_name or "Игрок"
    if user_id not in users_data:
        users_data[user_id] = {"balance": 507000, "bandit_history": [], "total_won_coins": 0, "total_lost_coins": 0}
    
    await message.answer(f"<b>{username}</b>\nМонеты: {users_data[user_id]['balance']} 🪙︎", parse_mode="HTML")

# Админ монета кошуу (+50000 ID)
@dp.message(F.text.startswith("+"))
async def admin_add_coins(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    parts = message.text.strip().split()
    if len(parts) >= 2:
        try:
            amount = int(parts[0].replace("+", ""))
            target_user_id = int(parts[1])
            if target_user_id not in users_data:
                users_data[target_user_id] = {"balance": 507000, "bandit_history": [], "total_won_coins": 0, "total_lost_coins": 0}
            users_data[target_user_id]["balance"] += amount
            await message.answer(f"👑 Админ: ID <code>{target_user_id}</code> балансына +{amount} 🪙 кошулду!", parse_mode="HTML")
        except ValueError:
            pass

# Монета которуу реплай аркылуу (+10000)
@dp.message(F.reply_to_message)
async def handle_transfer(message: types.Message):
    text = message.text.strip().replace(" ", "").lower()
    if text in ["+10000", "+10000монет", "+10к"]:
        sender_id = message.from_user.id
        sender_name = message.from_user.first_name or "Игрок"
        recipient_user = message.reply_to_message.from_user
        recipient_id = recipient_user.id
        recipient_name = recipient_user.first_name or "Игрок"

        if sender_id == recipient_id:
            await message.answer("❌ Өзүңүзгө монета которо албайсыз!")
            return

        today_date = datetime.now().strftime("%Y-%m-%d")
        if daily_transfer_limits.get(sender_id) == today_date:
            await message.answer("⚠️ Лимит! Күнүнө 1 эле жолу монета бере аласыз.")
            return

        if sender_id not in users_data:
            users_data[sender_id] = {"balance": 507000, "bandit_history": [], "total_won_coins": 0, "total_lost_coins": 0}
        
        if users_data[sender_id]["balance"] < 10000:
            await message.answer("❌ Балансыңызда каражат жетишсиз!")
            return

        if recipient_id not in users_data:
            users_data[recipient_id] = {"balance": 507000, "bandit_history": [], "total_won_coins": 0, "total_lost_coins": 0}

        users_data[sender_id]["balance"] -= 10000
        users_data[recipient_id]["balance"] += 10000
        daily_transfer_limits[sender_id] = today_date

        await message.answer(f"✅ <b>{sender_name}</b> -> <b>{recipient_name}</b> багытына 10,000 🪙 которулду!", parse_mode="HTML")
        return

async def main():
    print("Бот ишке кирди!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
