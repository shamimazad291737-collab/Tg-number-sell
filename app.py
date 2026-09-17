import os
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# লোগিং সেটআপ
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# এনভায়রনমেন্ট ভেরিয়েবল
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SIM5_API_TOKEN = os.getenv("SIM5_API_TOKEN")

SIM5_HEADERS = {
    "Authorization": f"Bearer {SIM5_API_TOKEN}",
    "Accept": "application/json"
}

# /start কমান্ড হ্যান্ডলার
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("👤 Check Balance", callback_data="check_balance")],
        [InlineKeyboardButton("🛒 Buy Number (Test)", callback_data="buy_test")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "স্বাগতম! 5sim বটে আপনাকে স্বাগতম। নিচের অপশনগুলো থেকে সিলেক্ট করুন:",
        reply_markup=reply_markup
    )

# বাটন ক্লিক হ্যান্ডলার
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "check_balance":
        try:
            url = "https://5sim.net/v1/user/profile"
            response = requests.get(url, headers=SIM5_HEADERS, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                email = data.get("email", "N/A")
                balance = data.get("balance", 0)
                rating = data.get("rating", 0)
                
                msg = f"📊 **Account Profile:**\n📧 Email: `{email}`\n💰 Balance: `{balance} RUB`\n⭐ Rating: `{rating}`"
                await query.edit_message_text(text=msg, parse_mode="Markdown")
            else:
                await query.edit_message_text(text="❌ API থেকে ডেটা আনতে সমস্যা হয়েছে। টোকেন চেক করুন।")
        except Exception as e:
            logger.error(f"Error fetching profile: {e}")
            await query.edit_message_text(text="⚠️ সার্ভারে কানেক্ট করতে সমস্যা হচ্ছে।")

    elif query.data == "buy_test":
        try:
            country = "england"
            operator = "any"
            product = "telegram"
            url = f"https://5sim.net/v1/user/buy/activation/{country}/{operator}/{product}"
            
            response = requests.get(url, headers=SIM5_HEADERS, timeout=10)
            if response.status_code == 200:
                order = response.json()
                order_id = order.get("id")
                phone = order.get("phone")
                price = order.get("price")
                
                msg = f"✅ **Order Successful!**\n🆔 Order ID: `{order_id}`\n📞 Number: `+{phone}`\n💵 Price: `{price} RUB`"
                await query.edit_message_text(text=msg, parse_mode="Markdown")
            else:
                err_msg = response.json().get("message", "Unknown error")
                await query.edit_message_text(text=f"❌ নাম্বার কেনা যায়নি!\nকারণ: {err_msg}")
        except Exception as e:
            logger.error(f"Error buying number: {e}")
            await query.edit_message_text(text="⚠️ নাম্বার কেনার সময় ত্রুটি ঘটেছে।")

def main() -> None:
    if not TELEGRAM_BOT_TOKEN or not SIM5_API_TOKEN:
        logger.error("Error: TELEGRAM_BOT_TOKEN বা SIM5_API_TOKEN সেট করা নেই!")
        return

    # টেলিগ্রাম অ্যাপ্লিকেশন বিল্ড করা
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))

    logger.info("Bot is starting via Polling...")
    application.run_polling()

if __name__ == "__main__":
    main()
    
