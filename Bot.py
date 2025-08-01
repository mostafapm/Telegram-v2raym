import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# فعال کردن لاگ برای دیباگ بهتر
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# گرفتن متغیرهای محیطی از هاست Render
# این روش امن‌تر از هاردکد کردن اطلاعات حساس است
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SOURCE_CHANNEL_ID = os.getenv("SOURCE_CHANNEL_ID")  # یوزرنیم کانال منبع، مثلاً "@public_channel_name"
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID") # شناسه عددی اکانت ادمین که کانفیگ‌ها را دریافت می‌کند

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """دستور /start را مدیریت می‌کند و به کاربر خوش‌آمد می‌گوید."""
    user_id = update.message.from_user.id
    await update.message.reply_text(
        f"سلام! من یک ربات فیلترکننده کانفیگ V2Ray هستم.\n"
        f"پست‌های کانال {SOURCE_CHANNEL_ID} را برای کانفیگ‌های 'reality' بررسی می‌کنم.\n"
        f"شناسه کاربری شما: `{user_id}`\n"
        f"از این شناسه برای تنظیم متغیر ADMIN_CHAT_ID در هاست استفاده کنید."
    )

async def handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """هر پست جدید در کانال را پردازش می‌کند."""
    # update.channel_post شامل پیام‌های ارسال شده در کانال است
    message = update.channel_post

    # فقط پیام‌های متنی را پردازش کن
    if message and message.text:
        post_text = message.text
        logger.info(f"دریافت پست از کانال: {SOURCE_CHANNEL_ID}")
        
        # کانفیگ‌ها را پیدا و فیلتر کن
        # هر خط از پیام را به عنوان یک کانفیگ احتمالی در نظر می‌گیریم
        configs = post_text.splitlines()
        reality_configs = []
        for config in configs:
            # شرط اصلی: باید 'vless://' در آن باشد و همچنین 'security=reality'
            if "vless://" in config and "security=reality" in config:
                reality_configs.append(config)
        
        # اگر کانفیگ reality پیدا شد، آن را برای ادمین ارسال کن
        if reality_configs:
            logger.info(f"پیدا شدن {len(reality_configs)} کانفیگ reality.")
            # کانفیگ‌ها را در یک پیام جمع کرده و ارسال کن
            full_message = "\n\n".join(reality_configs)
            try:
                await context.bot.send_message(
                    chat_id=ADMIN_CHAT_ID,
                    text=f"✅ کانفیگ‌های Reality جدید پیدا شد:\n\n{full_message}"
                )
            except Exception as e:
                logger.error(f"خطا در ارسال پیام به ادمین: {e}")
        else:
            logger.info("هیچ کانفیگ reality در این پست یافت نشد.")


def main() -> None:
    """ربات را اجرا می‌کند."""
    if not TOKEN or not SOURCE_CHANNEL_ID or not ADMIN_CHAT_ID:
        logger.error("یکی از متغیرهای محیطی (TOKEN, SOURCE_CHANNEL_ID, ADMIN_CHAT_ID) تنظیم نشده است!")
        return

    # ساخت اپلیکیشن ربات
    application = Application.builder().token(TOKEN).build()

    # افزودن دستورات
    application.add_handler(CommandHandler("start", start))
    
    # افزودن پردازشگر برای پست‌های کانال
    # ما از فیلتر `Chat` برای مشخص کردن کانال منبع استفاده می‌کنیم
    application.add_handler(MessageHandler(
        filters.UpdateType.CHANNEL_POST & filters.Chat(username=SOURCE_CHANNEL_ID.lstrip('@')), 
        handle_channel_post
    ))

    # اجرای ربات تا زمانی که متوقف شود
    logger.info("ربات در حال اجراست...")
    application.run_polling()


if __name__ == "__main__":
    main()

