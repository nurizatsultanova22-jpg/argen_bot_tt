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
    return "Mini-Roulette & Bandit Bot is active!"

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
        ],
        [
            InlineKeyboardButton("💎 Донат", url="https://t.me/argen") # Өзүңүздүн юзериңизди жазыңыз
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_user(user_id, name="Игрок"):
    if user_id not in users_data:
        users_data[user_id] = {
            "name": name,
            "balance": 5000,  # Баштапкы баланс 5000
            "last_bet": ("red", 1000),
            "history": []
        }
    return users_data[user_id]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data = get_user(user.id, user.first_name)
    bal = user_data["balance"]
    
    text = (
        f"🎰 *Минирулетка*\n"
        f"Баланс: {bal} 🌕\n\n"
        f"Угадайте число из:\n"
        f"0🟢\n"
        f"1🔴 2⚫ 3🔴 4⚫ 5🔴 6⚫\n"
        f"7🔴 8⚫ 9🔴 10⚫ 11🔴 12⚫\n\n"
        f"💬 *Команды:*\n"
        f"• `б` — Посмотреть баланс\n"
        f"• `лог` — История рулетки\n"
        f"• `Бандит` — Слот игра (ставка 500)\n"
        f"• `1000 к` или `1000 ч` — Ставки (красное/чёрное)\n"
        f"• `+ 500 @юзер` — Перевод монет игроку"
    )
    
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=get_keyboard())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    text_lower = text.lower()
    user = update.effective_user
    user_data = get_user(user.id, user.first_name)

    # 1. Баланс текшерүү ("б")
    if text_lower in ["б", "баланс"]:
        await update.message.reply_text(f"KNK-{user_data['name']}\nМонеты: {user_data['balance']}🌕")
        return

    # 2. Лог / История
    if text_lower in ["лог", "история"]:
        history = user_data["history"]
        if not history:
            await update.message.reply_text("📜 История пуста, сыграйте в рулетку!")
        else:
            log_text = "\n".join(history[-10:])
            await update.message.reply_text(log_text)
        return

    # 3. Перевод монет другим (+ 500 @юзер же через реплай)
    if text.startswith("+"):
        parts = text.split()
        if len(parts) >= 2:
            try:
                transfer_amt = int(parts[1])
                target_user_id = None
                target_name = "Игрок"

                # Эгер юзер отмечено болсо же реплай кылынса
                if update.message.reply_to_message:
                    target_user_id = update.message.reply_to_message.from_user.id
                    target_name = update.message.reply_to_message.from_user.first_name
                elif len(parts) >= 3 and parts[2].startswith("@"):
                    target_username = parts[2].lstrip("@").lower()
                    for uid, udata in users_data.items():
                        if udata.get("username", "").lower() == target_username:
                            target_user_id = uid
                            target_name = udata["name"]
                            break

                if not target_user_id:
                    await update.message.reply_text("❌ Укажите пользователя через ответ на сообщение или по тегу (@username).")
                    return

                if user_data["balance"] < transfer_amt:
                    await update.message.reply_text("❌ У вас недостаточно монет для перевода!")
                    return

                # Акчаны которуу
                user_data["balance"] -= transfer_amt
                target_data = get_user(target_user_id, target_name)
                target_data["balance"] += transfer_amt

                await update.message.reply_text(f"✅ Успешно переведено {transfer_amt} 🌕 игроку {target_name}!")
                return
            except ValueError:
                pass

    # 4. Бандит (слоты)
    if text_lower in ["бандит", "bandit"]:
        bet_amt = 500
        if user_data["balance"] < bet_amt:
            await update.message.reply_text("❌ Недостаточно средств! (Нужно 500 🌕)")
            return

        symbols = ["🎴", "♠️", "🀄", "🀄", "❤️", "🔔", "🍋", "⭐"]
        slot_res = [random.choice(symbols) for _ in range(4)]
        slot_line = "".join(slot_res)

        if slot_res[0] == slot_res[1] == slot_res[2] == slot_res[3]:
            win_amt = bet_amt * 5
            user_data["balance"] += win_amt
            result_str = f"Выигрыш: +{win_amt} 🌕"
        elif slot_res[0] == slot_res[1] or slot_res[2] == slot_res[3]:
            win_amt = bet_amt * 2
            user_data["balance"] += win_amt
            result_str = f"Выигрыш: +{win_amt} 🌕"
        else:
            user_data["balance"] -= bet_amt
            result_str = f"Проигрыш: {bet_amt} 🌕"

        reply_text = f"KNK-{user_data['name']}\n\n{slot_line}\n\n{result_str}"
        await update.message.reply_text(reply_text)
        return

    # 5. Ставки текстом: "1000 к", "1000 ч", "5000 на 12" ж.б.
    parts = text_lower.split()
    if len(parts) >= 2:
        try:
            amt = int(parts[0])
            target = parts[1]

            if target in ["к", "кр", "красное", "красный"]:
                bet_type = "red"
                target_name = "красное 🔴"
            elif target in ["ч", "черное", "черный"]:
                bet_type = "black"
                target_name = "чёрное ⚫"
            elif target in ["на"]:
                # Эски формат: "5000 на 12"
                if len(parts) >= 3:
                    target = parts[2]
                    bet_type = "red" if target in ["красное", "red"] else ("black" if target in ["черное", "black"] else target)
                    target_name = target
                else:
                    return
            else:
                bet_type = target
                target_name = target

            user_data["last_bet"] = (bet_type, amt)
            await update.message.reply_text(f"✅ Ставка принята: {amt} на {target_name}\nНажмите 'Крутить' для запуска.", reply_markup=get_keyboard())
            return
        except ValueError:
            pass

    if text_lower == "рулетка":
        await start(update, context)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    user_data = get_user(user.id, user.first_name)

    data = query.data

    if data.startswith("bet_"):
        bet_type = data.split("_")[1]
        user_data["last_bet"] = (bet_type, 1000)
        await query.answer(f"Ставка принята: 1000 на {bet_type}!", show_alert=False)
        return

    if data.startswith("range_"):
        user_data["last_bet"] = (data, 1000)
        await query.answer("Диапазон установлен (1000 🌕)", show_alert=False)
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
            await query.answer("❌ Недостаточно средств на балансе!", show_alert=True)
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

        user_data["history"].append(f"{roll}{color}")

        won = False
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
            multiplier = 10 if str(bet_type) == str(roll) else 2
            win_amt = bet_amt * multiplier
            user_data["balance"] += win_amt
            result_text = f"🎉 Рулетка: {roll}{color}\nВы выиграли! +{win_amt} 🌕"
        else:
            user_data["balance"] -= bet_amt
            result_text = f"❌ Рулетка: {roll}{color}\nВы проиграли (-{bet_amt} 🌕)"

        bal = user_data["balance"]
        text = (
            f"{result_text}\n\n"
            f"🎰 *Минирулетка*\n"
            f"Баланс: {bal} 🌕\n\n"
            f"Угадайте число из:\n"
            f"0🟢\n"
            f"1🔴 2⚫ 3🔴 4⚫ 5🔴 6⚫\n"
            f"7🔴 8⚫ 9🔴 10⚫ 11🔴 12⚫"
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
