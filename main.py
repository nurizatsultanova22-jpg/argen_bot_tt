import os
import threading
import random
from flask import Flask
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, MessageHandler, CommandHandler, filters, ContextTypes

TELEGRAM_TOKEN = "8943857517:AAHKx8raz2WrxYeHI2hjE1f5TpnygJq2vZE"

users_data = {}

app_web = Flask(__name__)
@app_web.route('/')
def home():
    return "Mini-Roulette Bot is active!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host="0.0.0.0", port=port)

def get_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("1 - 3", callback_data="range_1_3"),
            InlineKeyboardButton("4 - 6", callback_data="range_4_6"),
            InlineKeyboardButton("7 - 9", callback_data="range_7_9"),
            InlineKeyboardButton("10 - 12", callback_data="range_10_12")
        ],
        [
            InlineKeyboardButton("1к на 🔴", callback_data="bet_red"),
            InlineKeyboardButton("1к на ⚫", callback_data="bet_black"),
            InlineKeyboardButton("1к на 0🟢", callback_data="bet_zero")
        ],
        [
            InlineKeyboardButton("Повторить", callback_data="repeat"),
            InlineKeyboardButton("Удвоить", callback_data="double"),
            InlineKeyboardButton("🔄 Крутить", callback_data="spin")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in users_data:
        users_data[user_id] = {"balance": 20000, "last_bet": ("red", 1000)}

    bal = users_data[user_id]["balance"]
    
    text = (
        f"🎰 *Минирулетка*\n"
        f"Баланс: {bal} 🌕\n\n"
        f"Угадайте число из:\n"
        f"0🟢\n"
        f"1🔴 2⚫ 3🔴 4⚫ 5🔴 6⚫\n"
        f"7🔴 8⚫ 9🔴 10⚫ 11🔴 12⚫\n\n"
        f"Ставки можно текстом:\n"
        f"`1000 на красное` | `5000 на 12`"
    )
    
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=get_keyboard())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    user_id = update.effective_user.id

    if user_id not in users_data:
        users_data[user_id] = {"balance": 20000, "last_bet": ("red", 1000)}

    # Текст аркылуу ставка коюу (мисалы: "5000 на 12" же "1000 на красное")
    parts = text.split()
    if len(parts) >= 3 and parts[1] == "на":
        try:
            amt = int(parts[0])
            target = parts[2]
            
            # Түстөрдү же сандарды кабыл алуу
            if target in ["красное", "красный", "red"]:
                bet_type = "red"
            elif target in ["черное", "черный", "black"]:
                bet_type = "black"
            elif target in ["зеленое", "зеленый", "zero", "0"]:
                bet_type = "zero"
            else:
                bet_type = target # Сан болушу мүмкүн (мисалы 12)

            users_data[user_id]["last_bet"] = (bet_type, amt)
            await update.message.reply_text(f"✅ Ставка кабыл алынды: {amt} на {target}\nЭми 'Крутить' баскычын басыңыз же рулетка деп жазыңыз.", reply_markup=get_keyboard())
            return
        except ValueError:
            pass

    if text == "рулетка":
        await start(update, context)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if user_id not in users_data:
        users_data[user_id] = {"balance": 20000, "last_bet": ("red", 1000)}

    data = query.data
    user_data = users_data[user_id]

    if data.startswith("bet_"):
        bet_type = data.split("_")[1]
        user_data["last_bet"] = (bet_type, 1000)
        await query.answer(f"Ставка кабыл алынды: 1000 на {bet_type}!", show_alert=False)
        return

    if data.startswith("range_"):
        user_data["last_bet"] = (data, 1000)
        await query.answer("Диапазон ставкага коюлду (1000 🌕)", show_alert=False)
        return

    if data == "double":
        t, amt = user_data["last_bet"]
        user_data["last_bet"] = (t, amt * 2)
        await query.answer(f"Ставка удвоена: {amt * 2}", show_alert=False)
        return

    if data == "spin":
        bal = user_data["balance"]
        bet_type, bet_amt = user_data["last_bet"]

        if bal < bet_amt:
            await query.answer("❌ Балансыңыз жетпейт!", show_alert=True)
            return

        roll = random.randint(0, 12)
        
        if roll == 0:
            color = "🟢"
            c_name = "zero"
        elif roll % 2 != 0:
            color = "🔴"
            c_name = "red"
        else:
            color = "⚫"
            c_name = "black"

        won = False
        # Түскө же санга текшерүү
        if str(bet_type) == str(roll):
            won = True
        elif bet_type == c_name:
            won = True
        elif bet_type == "range_1_3" and 1 <= roll <= 3:
            won = True
        elif bet_type == "range_4_6" and 4 <= roll <= 6:
            won = True
        elif bet_type == "range_7_9" and 7 <= roll <= 9:
            won = True
        elif bet_type == "range_10_12" and 10 <= roll <= 12:
            won = True

        if won:
            # Эгер так санга утса көбүрөөк, түскө утса эки эсе беребиз
            multiplier = 10 if str(bet_type) == str(roll) else 2
            win_amt = bet_amt * multiplier
            user_data["balance"] += win_amt
            result_text = f"🎉 Рулетка: {roll}{color}\nСиз уттуңуз! +{win_amt} 🌕"
        else:
            user_data["balance"] -= bet_amt
            result_text = f"❌ Рулетка: {roll}{color}\nТилекке каршы, уттурдуңуз (-{bet_amt} 🌕)"

        bal = user_data["balance"]
        text = (
            f"{result_text}\n\n"
            f"🎰 *Минирулетка*\n"
            f"Баланс: {bal} 🌕\n\n"
            f"Угадайте число из:\n"
            f"0🟢\n"
            f"1🔴 2⚫ 3🔴 4⚫ 5🔴 6⚫\n"
            f"7🔴 8⚫ 9🔴 10⚫ 11🔴 12⚫\n\n"
            f"Ставки можно текстом:\n"
            f"`1000 на красное` | `5000 на 12`"
        )
        try:
            await query.message.edit_text(text, parse_mode="Markdown", reply_markup=get_keyboard())
        except Exception:
            pass

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()
