import os
import logging
import requests
import time
from pymongo import MongoClient
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
MONGODB_URI = os.environ.get("MONGODB_URI")
IDPAY_CALLBACK_URL = os.environ.get("CALLBACK_URL", "https://yourdomain.com/callback")

client = MongoClient(MONGODB_URI)
db = client["telegram_bot"]
users_col = db["users"]

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash-lite")

SYSTEM_PROMPT = "تو یک متخصص تفسیر خواب هستی. فقط و فقط تفسیر خواب انجام میدی. خواب‌ها را بر اساس روان‌شناسی نمادین و تحلیل علمی تفسیر میکنی. نمادها، احساسات و تصاویر خواب را به صورت علمی و روان‌شناختی تحلیل کن. اگه کسی چیز دیگه‌ای پرسید، مودبانه بگو که فقط تفسیر خواب بلدی. جواب‌هات رو به فارسی روان و کامل بده."

FREE_CREDITS = 1

PACKAGES = [
    {"id": "1", "label": "1 تعبیر - 20,000 تومان", "count": 1, "amount": 200000},
    {"id": "2", "label": "3 تعبیر - 50,000 تومان", "count": 3, "amount": 500000},
    {"id": "3", "label": "6 تعبیر - 100,000 تومان", "count": 6, "amount": 1000000},
]

chat_sessions = {}

def get_user(user_id):
    uid = str(user_id)
    user = users_col.find_one({"_id": uid})
    if not user:
        user = {"_id": uid, "credits": FREE_CREDITS, "pending": {}}
        users_col.insert_one(user)
    return user

def update_user(user_id, data):
    users_col.update_one({"_id": str(user_id)}, {"$set": data})

def main_keyboard():
    keyboard = [
        [KeyboardButton("درباره تعبیر خواب  "), KeyboardButton("خواب جدید")],
        [KeyboardButton("استعلام اعتبار"), KeyboardButton("افزایش اعتبار")],
        [KeyboardButton("پشتیبانی")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True)

def package_keyboard():
    keyboard = [[KeyboardButton(p["label"])] for p in PACKAGES]
    keyboard.append([KeyboardButton("بازگشت")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    footer = "\n\nاعتبار باقی‌مانده: " + str(new_credits) + " تعبیر"
        chunks = [reply[i:i+3800] for i in range(0, len(reply), 3800)]
        for i, chunk in enumerate(chunks):
            if i == len(chunks) - 1:
                await update.message.reply_text("تفسیر خواب:\n\n" + chunk + footer, reply_markup=main_keyboard())
            else:
                await update.message.reply_text("تفسیر خواب:\n\n" + chunk)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    user = get_user(user_id)

    if text == "درباره تعبیر خواب":
        await update.message.reply_text(
            "درباره تفسیر خواب\n\n"
            "خواب‌ها انواع مختلف دارند.\n"
            "بعضی فقط مرور اتفاقات روزمره هستند و بعضی تشویش ذهن.\n"
            "برخی دیگر اما خواب‌های نمادینند که از عمق ضمیر ناخودآگاه انسان می‌آیند.\n"
            "تنها این دسته از خواب‌ها ارزش تعبیر دارند.\n\n"
            "ربات تعبیر خواب علمی تلاش می‌کند با تعبیر نمادها و نشانه‌ها و با کمک منابع علمی دریچه‌ای به سوی شناخت رویاها باز نماید.\n"
            "به همین خاطر اعتبار خریداری شده‌ی شما تنها برای خواب‌های نمادین استفاده می‌شود.\n\n"
            "درعین حال باید بدانیم تعبیر خواب بیشتر جنبه‌ی سرگرمی داشته و قطعیت علمی ندارد.",
            reply_markup=main_keyboard()
        )
        return

    if text == "خواب جدید":
        if user_id in chat_sessions:
            del chat_sessions[user_id]
        await update.message.reply_text(
            "آماده‌ام! خواب جدیدت رو برام تعریف کن:",
            reply_markup=main_keyboard()
        )
        return

    if text == "استعلام اعتبار":
        await update.message.reply_text(
            "اعتبار شما\n\n"
            "تعداد تعبیر باقی‌مانده: " + str(user['credits']) + " تعبیر\n\n"
            "برای افزایش اعتبار روی افزایش اعتبار بزن.",
            reply_markup=main_keyboard()
        )
        return

    if text == "افزایش اعتبار":
        await update.message.reply_text(
            "پکیج‌های اعتبار\n\nیکی از پکیج‌های زیر رو انتخاب کن:",
            reply_markup=package_keyboard()
        )
        return

    if text == "پشتیبانی":
        await update.message.reply_text(
            "پشتیبانی\n\n"
            "برای ارتباط با ادمین:\n"
            "@mf1361\n\n"
            "در صورت بروز مشکل در پرداخت یا هر سوالی، مستقیم پیام بدید.",
            reply_markup=main_keyboard()
        )
        return

    if text == "بازگشت":
        await update.message.reply_text("به منو اصلی برگشتی", reply_markup=main_keyboard())
        return

    for pkg in PACKAGES:
        if text == pkg["label"]:
            if not IDPAY_API_KEY:
                await update.message.reply_text(
                    "درگاه پرداخت هنوز راه‌اندازی نشده.\n"
                    "برای خرید اعتبار با پشتیبانی تماس بگیر:\n@mf1361",
                    reply_markup=main_keyboard()
                )
                return
            try:
                response = requests.post(
                    "https://api.idpay.ir/v1.1/payment",
                    headers={"X-API-KEY": IDPAY_API_KEY, "Content-Type": "application/json"},
                    json={
                        "order_id": str(user_id) + "_" + pkg["id"] + "_" + str(int(time.time())),
                        "amount": pkg["amount"],
                        "callback": IDPAY_CALLBACK_URL,
                        "desc": "خرید " + str(pkg["count"]) + " تعبیر خواب"
                    }
                )
                data = response.json()
                if "link" in data:
                    update_user(user_id, {"pending." + data.get("id", ""): pkg["count"]})
                    await update.message.reply_text(
                        "لینک پرداخت:\n\n" + data["link"] + "\n\n"
                        "پکیج: " + pkg["label"] + "\n"
                        "بعد از پرداخت، اعتبار به حسابت اضافه میشه.",
                        reply_markup=main_keyboard()
                    )
                else:
                    raise Exception(str(data))
            except Exception as e:
                logging.error("IDPay error: " + str(e))
                await update.message.reply_text(
                    "مشکلی در اتصال به درگاه پرداخت پیش اومد.\nبا پشتیبانی تماس بگیر: @mf1361",
                    reply_markup=main_keyboard()
                )
            return

    if user["credits"] <= 0:
        await update.message.reply_text(
            "اعتبار شما تموم شده!\n\nبرای ادامه، اعتبار بخر",
            reply_markup=package_keyboard()
        )
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        if user_id not in chat_sessions:
            chat_sessions[user_id] = []
        chat_sessions[user_id].append("کاربر: " + text)
        full_prompt = SYSTEM_PROMPT + "\n\n" + "\n".join(chat_sessions[user_id][-6:])
        response = model.generate_content(full_prompt)
        reply = response.text
        chat_sessions[user_id].append("ربات: " + reply)
        new_credits = user["credits"] - 1
        update_user(user_id, {"credits": new_credits})
        await update.message.reply_text(
            "تفسیر خواب:\n\n" + reply + "\n\n"
            "اعتبار باقی‌مانده: " + str(new_credits) + " تعبیر",
            reply_markup=main_keyboard()
        )
    except Exception as e:
        import traceback
        logging.error("خطا: " + str(e) + "\n" + traceback.format_exc())
        await update.message.reply_text(
            "متاسفم، مشکلی پیش اومد. دوباره امتحان کن.",
            reply_markup=main_keyboard()
        )

async def add_credit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("شما ادمین نیستید.")
        return
    try:
        target_id = str(context.args[0])
        amount = int(context.args[1])
        user = get_user(target_id)
        new_credits = user["credits"] + amount
        update_user(target_id, {"credits": new_credits})
        await update.message.reply_text(str(amount) + " اعتبار به کاربر " + target_id + " اضافه شد.\nاعتبار جدید: " + str(new_credits))
        try:
            await context.bot.send_message(
                chat_id=int(target_id),
                text=str(amount) + " اعتبار تعبیر خواب به حساب شما اضافه شد!\nاعتبار فعلی: " + str(new_credits) + " تعبیر"
            )
        except:
            pass
    except:
        await update.message.reply_text("فرمت: /addcredit [user_id] [amount]")

async def users_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("شما ادمین نیستید.")
        return
    count = users_col.count_documents({})
    text = "تعداد کاربران: " + str(count) + "\n\n"
    for u in users_col.find().limit(20):
        text += str(u["_id"]) + " - اعتبار: " + str(u["credits"]) + "\n"
    await update.message.reply_text(text)

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addcredit", add_credit))
    app.add_handler(CommandHandler("users", users_list))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("ربات روشن شد!")
    app.run_polling()

if __name__ == "__main__":
    main()
