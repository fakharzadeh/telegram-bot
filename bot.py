import os
import json
import logging
import requests
import google.generativeai as genai
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
IDPAY_API_KEY = os.environ.get("IDPAY_API_KEY")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

IDPAY_CALLBACK_URL = os.environ.get("CALLBACK_URL", "https://yourdomain.com/callback")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash-lite")

SYSTEM_PROMPT = "تو یک متخصص تعبیر خواب هستی. فقط و فقط تعبیر خواب انجام می‌دی. خواب‌ها را بر اساس تعابیر اسلامی و سنتی تفسیر می‌کنی. اگه کسی چیز دیگه‌ای پرسید، مودبانه بگو که فقط تعبیر خواب بلدی. جواب‌هات رو به فارسی روان و کامل بده."

FREE_CREDITS = 1
DATA_FILE = "users.json"

PACKAGES = [
    {"id": "1", "label": "۱ تعبیر — ۲۰,۰۰۰ تومان", "count": 1, "amount": 200000},
    {"id": "2", "label": "۳ تعبیر — ۵۰,۰۰۰ تومان", "count": 3, "amount": 500000},
    {"id": "3", "label": "۶ تعبیر — ۱۰۰,۰۰۰ تومان", "count": 6, "amount": 1000000},
]

def load_users():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def get_user(users, user_id):
    uid = str(user_id)
    if uid not in users:
        users[uid] = {"credits": FREE_CREDITS, "history": [], "pending": {}}
    if "pending" not in users[uid]:
        users[uid]["pending"] = {}
    return users[uid]

def main_keyboard():
    keyboard = [
        [KeyboardButton("📖 درباره تعبیر خواب"), KeyboardButton("🌙 خواب جدید")],
        [KeyboardButton("💳 استعلام اعتبار"), KeyboardButton("➕ افزایش اعتبار")],
        [KeyboardButton("🆘 پشتیبانی")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, persistent=True)

def package_keyboard():
    keyboard = [[KeyboardButton(p["label"])] for p in PACKAGES]
    keyboard.append([KeyboardButton("🔙 بازگشت")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_users()
    user = get_user(users, update.effective_user.id)
    save_users(users)
    await update.message.reply_text(
        f"سلام {update.effective_user.first_name} عزیز! 🌙\n\n"
        f"به ربات تعبیر خواب خوش اومدی!\n"
        f"اعتبار فعلی شما: {user['credits']} تعبیر\n\n"
        "خوابت رو بنویس تا تعبیرش کنم 🔮",
        reply_markup=main_keyboard()
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    users = load_users()
    user = get_user(users, user_id)

    # دکمه‌های منو
    if text == "📖 درباره تعبیر خواب":
        await update.message.reply_text(
            "🌙 *درباره تعبیر خواب*\n\n"
            "تعبیر خواب علمی است که به تفسیر خواب‌های انسان می‌پردازد.\n\n"
            "این ربات با استفاده از هوش مصنوعی و منابع معتبر اسلامی و سنتی، خواب‌های شما را تعبیر می‌کند.\n\n"
            "📌 *نحوه استفاده:*\n"
            "کافیه خوابت رو با جزئیات بنویسی تا تعبیرش کنم!\n\n"
            "💡 هرچه جزئیات بیشتری بدی، تعبیر دقیق‌تری دریافت می‌کنی.",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )
        return

    if text == "🌙 خواب جدید":
        user["history"] = []
        save_users(users)
        await update.message.reply_text(
            "🌙 آماده‌ام! خواب جدیدت رو برام تعریف کن:",
            reply_markup=main_keyboard()
        )
        return

    if text == "💳 استعلام اعتبار":
        await update.message.reply_text(
            f"💳 *اعتبار شما*\n\n"
            f"تعداد تعبیر باقی‌مانده: *{user['credits']} تعبیر*\n\n"
            "برای افزایش اعتبار روی ➕ افزایش اعتبار بزن.",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )
        return

    if text == "➕ افزایش اعتبار":
        await update.message.reply_text(
            "💰 *پکیج‌های اعتبار*\n\n"
            "یکی از پکیج‌های زیر رو انتخاب کن:",
            parse_mode="Markdown",
            reply_markup=package_keyboard()
        )
        return

    if text == "🆘 پشتیبانی":
        await update.message.reply_text(
            "🆘 *پشتیبانی*\n\n"
            "برای ارتباط با ادمین:\n"
            "👤 @mf1361\n\n"
            "در صورت بروز مشکل در پرداخت یا هر سوالی، مستقیم پیام بدید.",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )
        return

    if text == "🔙 بازگشت":
        await update.message.reply_text(
            "به منو اصلی برگشتی 🏠",
            reply_markup=main_keyboard()
        )
        return

    # انتخاب پکیج
    for pkg in PACKAGES:
        if text == pkg["label"]:
            if not IDPAY_API_KEY:
                await update.message.reply_text(
                    "⚠️ درگاه پرداخت هنوز راه‌اندازی نشده.\n"
                    "برای خرید اعتبار با پشتیبانی تماس بگیر:\n👤 @mf1361",
                    reply_markup=main_keyboard()
                )
                return

            try:
                response = requests.post(
                    "https://api.idpay.ir/v1.1/payment",
                    headers={
                        "X-API-KEY": IDPAY_API_KEY,
                        "Content-Type": "application/json"
                    },
                    json={
                        "order_id": f"{user_id}_{pkg['id']}_{int(__import__('time').time())}",
                        "amount": pkg["amount"],
                        "callback": IDPAY_CALLBACK_URL,
                        "desc": f"خرید {pkg['count']} تعبیر خواب"
                    }
                )
                data = response.json()
                if "link" in data:
                    payment_id = data.get("id", "")
                    user["pending"][payment_id] = pkg["count"]
                    save_users(users)
                    await update.message.reply_text(
                        f"✅ *لینک پرداخت آماده‌ست:*\n\n"
                        f"پکیج: {pkg['label']}\n\n"
                        f"🔗 {data['link']}\n\n"
                        "بعد از پرداخت، اعتبار به حسابت اضافه می‌شه.",
                        parse_mode="Markdown",
                        reply_markup=main_keyboard()
                    )
                else:
                    raise Exception(str(data))
            except Exception as e:
                logging.error(f"IDPay error: {e}")
                await update.message.reply_text(
                    "مشکلی در اتصال به درگاه پرداخت پیش اومد.\n"
                    "با پشتیبانی تماس بگیر: @mf1361",
                    reply_markup=main_keyboard()
                )
            return

    # تعبیر خواب
    if user["credits"] <= 0:
        await update.message.reply_text(
            "⚠️ اعتبار شما تموم شده!\n\n"
            "برای ادامه، اعتبار بخر 👇",
            reply_markup=package_keyboard()
        )
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        chat = model.start_chat(history=user.get("history", []))
        response = chat.send_message(f"{SYSTEM_PROMPT}\n\nخواب کاربر: {text}")
        reply = response.text
        user["history"] = chat.history
        user["credits"] -= 1
        save_users(users)

        await update.message.reply_text(
            f"🔮 *تعبیر خواب:*\n\n{reply}\n\n"
            f"💳 اعتبار باقی‌مانده: {user['credits']} تعبیر",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )
    except Exception as e:
        logging.error(f"خطا: {e}")
        await update.message.reply_text(
            "متأسفم، مشکلی پیش اومد. دوباره امتحان کن.",
            reply_markup=main_keyboard()
        )

async def add_credit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ شما ادمین نیستید.")
        return
    try:
        target_id = str(context.args[0])
        amount = int(context.args[1])
        users = load_users()
        user = get_user(users, target_id)
        user["credits"] += amount
        save_users(users)
        await update.message.reply_text(f"✅ {amount} اعتبار به کاربر {target_id} اضافه شد.")
        try:
            await context.bot.send_message(
                chat_id=int(target_id),
                text=f"🎉 {amount} اعتبار تعبیر خواب به حساب شما اضافه شد!\nاعتبار فعلی: {user['credits']} تعبیر"
            )
        except:
            pass
    except:
        await update.message.reply_text("❌ فرمت اشتباه.\nاستفاده: /addcredit [user_id] [amount]")

async def users_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ شما ادمین نیستید.")
        return
    users = load_users()
    text = f"👥 تعداد کاربران: {len(users)}\n\n"
    for uid, data in list(users.items())[:20]:
        text += f"🆔 {uid} — اعتبار: {data['credits']}\n"
    await update.message.reply_text(text)

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addcredit", add_credit))
    app.add_handler(CommandHandler("users", users_list))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("ربات روشن شد! ✅")
    app.run_polling()

if __name__ == "__main__":
    main()
