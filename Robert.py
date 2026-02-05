import logging
import os
from telegram import Update, ForceReply
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# (((((تنظیمات)))))
OWNER_CHAT_ID = <@hosseinrasoly>  
BOT_TOKEN = os.environ.get("8296663525:AAF6CS44PoHq5HU4dgHEGDJ_5-Zs8m8HiRw")

# ((((((((لاگ))))))))
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ((((((((((مراحل Conversation))))))))))
ASK_MESSAGE = 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "سلام! لطفاً پیام خود را بنویسید تا برای صاحب ربات ارسال شود.",
        reply_markup=ForceReply(selective=True)
    )
    return ASK_MESSAGE

async def receive_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    text = update.message.text

    
    try:
        await context.bot.send_message(
            chat_id=OWNER_CHAT_ID,
            text=f"پیام جدید از {user.full_name} (@{user.username}):\n\n{text}"
        )
        await update.message.reply_text(
            "پیام شما با موفقیت ارسال شد! اگر لازم بود پاسخی دریافت می‌کنید."
        )
    except Exception as e:
        logging.error(f"Error sending message to owner: {e}")
        await update.message.reply_text(
            "متأسفانه مشکلی پیش آمد و پیام شما ارسال نشد."
        )

    
    return ASK_MESSAGE

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("عملیات لغو شد. برای ارسال پیام جدید /start بزنید.")
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ASK_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_message)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    app.add_handler(conv_handler)
    print("Bot is running...")
    app.run_polling()  

if __name__ == '__main__':
    main()
