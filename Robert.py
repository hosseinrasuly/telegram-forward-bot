# relay_bot.py
# نیازمندی: python-telegram-bot>=20
import logging
import json
import asyncio
from pathlib import Path
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ---------- پیکربندی ----------
BOT_TOKEN = "8296663525:AAF6CS44PoHq5HU4dgHEGDJ_5-Zs8m8HiRw"
OWNER_CHAT_ID = "@hosseinrasoly " # آیدی عددی خودت را اینجا بگذار
STATE_FILE = Path("relay_state.json")  # برای نگهداری موقتی مپ‌کردن‌ها (اختیاری)

# ---------- لاگ ----------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ---------- وضعیت در حافظه برای جواب به فرستنده ----------
# format: waiting_reply_from_owner = { owner_id: target_user_id }
waiting_reply_from_owner = {}
# optional persisting (simple)
def load_state():
    if STATE_FILE.exists():
        try:
            data = json.loads(STATE_FILE.read_text(encoding="utf8"))
            return data.get("waiting_reply_from_owner", {})
        except Exception:
            return {}
    return {}

def save_state():
    STATE_FILE.write_text(json.dumps({"waiting_reply_from_owner": waiting_reply_from_owner}), encoding="utf8")

# ---------- هندلرها ----------
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if update.effective_chat.id == OWNER_CHAT_ID:
        await update.message.reply_text("ربات رله فعال است. هر پیامی که به ربات بیاد، به شما فوروارد/کپی خواهد شد.")
    else:
        text = (
            "سلام! پیام شما دریافت شد.\n\n"
            "پیام شما به صاحب ربات ارسال خواهد شد. اگر لازم شد پاسخی از طرف صاحب دریافت می‌کنید."
        )
        await update.message.reply_text(text)

async def any_message_from_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    وقتی هر کسی (غیر از صاحب) پیام زد، این اجرا میشه و محتوا رو به OWNER می‌فرسته.
    از copy_message استفاده می‌کنیم تا انواع رسانه/سنتی/ویس و ... کار کنه.
    """
    msg = update.message
    sender = update.effective_user
    chat_id = update.effective_chat.id

    # اگر پیام از صاحب بود و او در حالت 'reply' باشد، پیام را برای مقصدِ ذخیره‌شده ارسال کن
    if chat_id == OWNER_CHAT_ID:
        # اگر منتظر پاسخ به یک کاربر بودیم، این پیام را به آن کاربر ارسال کن
        target = waiting_reply_from_owner.get(chat_id)
        if target:
            try:
                # برای ارسال متن/رسانه از copy_message یا send_message استفاده کن
                if msg.text:
                    await context.bot.send_message(chat_id=target, text=f"پیام از صاحب: \n\n{msg.text}")
                else:
                    # برای رسانه‌ها از copy_message استفاده می‌کنیم (ارسال بدون نشان دادن صاحب)
                    await context.bot.copy_message(chat_id=target, from_chat_id=msg.chat_id, message_id=msg.message_id)
                # تایید به صاحب
                await msg.reply_text("پیام شما به کاربر ارسال شد.")
            except Exception as e:
                await msg.reply_text(f"خطا در ارسال پیام: {e}")
            finally:
                # پاک کردن حالت انتظار
                waiting_reply_from_owner.pop(chat_id, None)
                save_state()
            return
        # در غیر این صورت، ادامه بدین (ممکنه صاحب به ربات پیام بده)
        await msg.reply_text("شما صاحب ربات هستید. برای پاسخ به یک کاربر، از دکمه‌ی 'Reply' که زیر پیام‌های ورودی می‌آید استفاده کنید.")
        return

    # اگر فرستنده صاحب نیست: کپی پیام به OWNER
    try:
        # نمایش اطلاعات مختصر فرستنده (ما به صورت نسبتاً ناشناس فقط نام/first+id هش‌شده می‌فرستیم)
        display_name = sender.full_name or "ناشناس"
        anon_id = f"user:{sender.id}"  # می‌تونیم اینو هش هم بکنیم اگر خواستی

        caption = f"پیامی از {display_name}\n{anon_id}\n\n"
        # دکمه‌های مدیریتی برای صاحب: Reply و Block (Block فقط نمونه)
        keyboard = InlineKeyboardMarkup(
            [[
                InlineKeyboardButton("✉️ Reply", callback_data=f"reply:{sender.id}"),
                InlineKeyboardButton("⛔ Block", callback_data=f"block:{sender.id}")
            ]]
        )

        # از copy_message استفاده می‌کنیم تا محتوای اصلی بدون تغییر بره برای صاحب
        await context.bot.copy_message(
            chat_id=OWNER_CHAT_ID,
            from_chat_id=msg.chat_id,
            message_id=msg.message_id,
            caption=caption if msg.text or msg.caption else caption,
            reply_markup=keyboard
        )

        # تایید به ارسال‌کننده (اختیاری، کمی شاعرانه!)
        await msg.reply_text("پیام شما ثبت شد؛ به زودی بررسی می‌شود. 🌙")
    except Exception as e:
        logger.exception("Error forwarding message")
        await msg.reply_text("خطا در ارسال پیام. لطفا بعداً تلاش کنید.")

async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data or ""
    user = q.from_user

    # فقط OWNER میتونه دکمه‌ها رو بزنه
    if user.id != OWNER_CHAT_ID:
        await q.edit_message_reply_markup(reply_markup=None)
        await q.message.reply_text("این دکمه فقط برای صاحب ربات است.")
        return

    if data.startswith("reply:"):
        target_id = int(data.split(":", 1)[1])
        waiting_reply_from_owner[user.id] = target_id
        save_state()
        await q.message.reply_text(f"حالا پیام خود را بفرستید — پیامی که ارسال کنید به کاربر ({target_id}) خواهد رفت.")
    elif data.startswith("block:"):
        target_id = int(data.split(":", 1)[1])
        # اینجا صرفاً نمونه: بلاک کردن کاربر (نیازمند منطق اضافه مثل نگهداری لیست بلاک)
        await q.message.reply_text(f" کاربر {target_id} به لیست بلاک اضافه شد (نمونه).")
    else:
        await q.message.reply_text("دکمه نامشخص.")

# ---------- main ----------
def main():
    # load persisted state if موجود
    global waiting_reply_from_owner
    waiting_reply_from_owner = load_state() or {}

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CallbackQueryHandler(callback_query_handler))
    # پیام‌های عادی (هر نوع) را بگیر
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, any_message_from_user))

    logger.info("ربات شروع به کار کرد.")
    app.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    main()
