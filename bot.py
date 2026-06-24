import os
import logging
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# تنظیمات لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# گرفتن متغیرها از محیط
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# تنظیم Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# نگه‌داشتن تاریخچه مکالمه برای هر کاربر
user_histories = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! 👋 من یه دستیار هوشمند هستم.\n"
        "هر سوالی داری بپرس، خوشحال می‌شم کمک کنم! 😊\n\n"
        "برای شروع مکالمه جدید بنویس: /new"
    )

async def new_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_histories[user_id] = []
    await update.message.reply_text("مکالمه جدید شروع شد! 🆕 بپرس چی می‌خوای.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text

    # نمایش حالت تایپ
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    # ساخت تاریخچه اگه نداشت
    if user_id not in user_histories:
        user_histories[user_id] = []

    try:
        # شروع چت با تاریخچه
        chat = model.start_chat(history=user_histories[user_id])
        response = chat.send_message(user_message)
        reply = response.text

        # ذخیره تاریخچه
        user_histories[user_id] = chat.history

        await update.message.reply_text(reply)

    except Exception as e:
        logging.error(f"خطا: {e}")
        await update.message.reply_text(
            "متأسفم، یه مشکلی پیش اومد. دوباره امتحان کن یا /new بنویس."
        )

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("new", new_chat))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("ربات روشن شد! ✅")
    app.run_polling()

if __name__ == "__main__":
    main()
