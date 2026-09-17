import os
import logging
import asyncio
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

# /start কমান্ড হ্যান্ডলার (মেইন মেনু)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("👤 Profile & Balance", callback_data="check_balance")],
        [InlineKeyboardButton("💳 Deposit (Crypto)", callback_data="deposit_crypto")],
        [InlineKeyboardButton("📊 Check Stock", callback_data="select_stock_country"),
         InlineKeyboardButton("🛒 Buy Number", callback_data="select_country")],
        [InlineKeyboardButton("🔍 Active Orders", callback_data="check_orders")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    msg = "🤖 **5sim Virtual Number Bot**\n\nনিচের অপশনগুলো থেকে সিলেক্ট করুন:"
    if update.message:
        await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.message.edit_text(msg, reply_markup=reply_markup, parse_mode="Markdown")

# বাটন ক্লিক হ্যান্ডলার
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "main_menu":
        await start(update, context)

    elif data == "check_balance":
        try:
            url = "https://5sim.net/v1/user/profile"
            response = requests.get(url, headers=SIM5_HEADERS, timeout=10)
            
            if response.status_code == 200:
                profile = response.json()
                email = profile.get("email", "N/A")
                balance = profile.get("balance", 0)
                rating = profile.get("rating", 0)
                
                msg = f"📊 **Account Profile:**\n📧 Email: `{email}`\n💰 Balance: `{balance} RUB`\n⭐ Rating: `{rating}`"
            else:
                msg = "❌ API থেকে ডেটা আনতে সমস্যা হয়েছে।"
            
            keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]]
            await query.edit_message_text(text=msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error fetching profile: {e}")
            await query.edit_message_text(text="⚠️ সার্ভারে কানেক্ট করতে সমস্যা হচ্ছে।")

    elif data == "deposit_crypto":
        msg = (
            "💳 **Crypto Deposit Instructions:**\n\n"
            "আপনার অ্যাকাউন্টে ব্যালেন্স যোগ করতে নিচের ক্রিপ্টো ওয়ালেট ঠিকানায় পেমেন্ট করুন:\n\n"
            "🪙 **USDT (TRC20):** `TYourCryptoWalletAddressHere12345`\n"
            "🪙 **LTC / BTC:** `LYourLitecoinAddressHere12345`\n\n"
            "📌 পেমেন্ট করার পর ট্রানজ্যাকশন আইডি (TxID) সহ অ্যাডমিনের সাথে যোগাযোগ করুন, ব্যালেন্স অ্যাড করে দেওয়া হবে।"
        )
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]]
        await query.edit_message_text(text=msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    # --- স্টক চেক করার জন্য কান্ট্রি সিলেকশন মেনু ---
    elif data == "select_stock_country":
        keyboard = [
            [InlineKeyboardButton("🇨🇴 Colombia", callback_data="stock_colombia"),
             InlineKeyboardButton("🇨🇳 China", callback_data="stock_china")],
            [InlineKeyboardButton("🇬🇧 England", callback_data="stock_england"),
             InlineKeyboardButton("🇷🇺 Russia", callback_data="stock_russia")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]
        ]
        await query.edit_message_text(text="📊 **Stock Check - Select Country:**\nকোন দেশের স্টক দেখতে চান সিলেক্ট করুন:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data.startswith("stock_"):
        country = data.split("_")[1]
        keyboard = [
            [InlineKeyboardButton("✈️ Telegram", callback_data=f"viewstock_{country}_telegram"),
             InlineKeyboardButton("💬 WhatsApp", callback_data=f"viewstock_{country}_whatsapp")],
            [InlineKeyboardButton("🌐 Google/Gmail", callback_data=f"viewstock_{country}_google"),
             InlineKeyboardButton("📘 Facebook", callback_data=f"viewstock_{country}_facebook")],
            [InlineKeyboardButton("🔙 Back to Countries", callback_data="select_stock_country")]
        ]
        await query.edit_message_text(text=f"📦 **Country:** `{country.capitalize()}`\nকোন সার্ভিসের স্টক দেখতে চান সিলেক্ট করুন:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data.startswith("viewstock_"):
        parts = data.split("_")
        country = parts[1]
        product = parts[2]
        
        try:
            url = f"https://5sim.net/v1/user/guest/products/{country}/{product}"
            response = requests.get(url, headers=SIM5_HEADERS, timeout=10)
            
            if response.status_code == 200:
                data_json = response.json()
                msg = f"📊 **Stock Details ({country.capitalize()} - {product.capitalize()}):**\n\n"
                
                # অপারেটর অনুযায়ী স্টক ও দামের তথ্য সাজানো
                found = False
                for operator, details in data_json.items():
                    count = details.get("count", 0)
                    price = details.get("price", 0)
                    if count > 0:
                        found = True
                        msg += f"🔹 **Operator:** `{operator}`\n   - Stock: `{count} avail.`\n   - Price: `{price} RUB`\n\n"
                
                if not found:
                    msg = f"❌ দুঃখিত! এই মুহূর্তে `{country.capitalize()}` এ `{product.capitalize()}` সার্ভিসের কোনো স্টক নেই।"
            else:
                msg = "❌ স্টক ইনফরমেশন আনতে সমস্যা হয়েছে।"
            
            keyboard = [[InlineKeyboardButton("🔙 Back to Stock Menu", callback_data="select_stock_country")]
                        [InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]]
            # Fix keyboard layout tuple list
            keyboard = [
                [InlineKeyboardButton("🔙 Back to Stock Menu", callback_data="select_stock_country")],
                [InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]
            ]
            await query.edit_message_text(text=msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error checking stock: {e}")
            await query.edit_message_text(text="⚠️ স্টক চেক করার সময় ত্রুটি ঘটেছে।")

    # --- নাম্বার কেনার মেনু ---
    elif data == "select_country":
        keyboard = [
            [InlineKeyboardButton("🇨🇴 Colombia", callback_data="country_colombia"),
             InlineKeyboardButton("🇨🇳 China", callback_data="country_china")],
            [InlineKeyboardButton("🇬🇧 England", callback_data="country_england"),
             InlineKeyboardButton("🇷🇺 Russia", callback_data="country_russia")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]
        ]
        await query.edit_message_text(text="🌍 **Select Country:**\nযে দেশের নাম্বার নিতে চান তা সিলেক্ট করুন:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data.startswith("country_"):
        country = data.split("_")[1]
        context.user_data['selected_country'] = country
        
        keyboard = [
            [InlineKeyboardButton("✈️ Telegram", callback_data=f"buy_{country}_telegram"),
             InlineKeyboardButton("💬 WhatsApp", callback_data=f"buy_{country}_whatsapp")],
            [InlineKeyboardButton("🌐 Google/Gmail", callback_data=f"buy_{country}_google"),
             InlineKeyboardButton("📘 Facebook", callback_data=f"buy_{country}_facebook")],
            [InlineKeyboardButton("🔙 Back to Countries", callback_data="select_country")]
        ]
        await query.edit_message_text(text=f"📦 **Selected Country:** `{country.capitalize()}`\nকোন সার্ভিসের জন্য নাম্বার চান সিলেক্ট করুন:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data.startswith("buy_"):
        parts = data.split("_")
        country = parts[1]
        product = parts[2]
        operator = "any"
        
        try:
            url = f"https://5sim.net/v1/user/buy/activation/{country}/{operator}/{product}"
            response = requests.get(url, headers=SIM5_HEADERS, timeout=10)
            
            if response.status_code == 200:
                order = response.json()
                order_id = order.get("id")
                phone = order.get("phone")
                price = order.get("price")
                
                keyboard = [
                    [InlineKeyboardButton("🔄 Check OTP / SMS", callback_data=f"check_sms_{order_id}")],
                    [InlineKeyboardButton("❌ Cancel Order (Refund)", callback_data=f"cancel_{order_id}")],
                    [InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]
                ]
                
                msg = (
                    f"✅ **Number Purchased Successfully!**\n\n"
                    f"🆔 Order ID: `{order_id}`\n"
                    f"📞 Number: `+{phone}`\n"
                    f"💵 Price: `{price} RUB`\n"
                    f"🌍 Country: `{country.capitalize()}` | Service: `{product.capitalize()}`\n\n"
                    f"⏳ ওটিপির জন্য অপেক্ষা করুন। কোড না আসলে **Cancel Order** বাটনে ক্লিক করে ব্যালেন্স রিফান্ড নিতে পারেন।"
                )
                await query.edit_message_text(text=msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
            else:
                err_msg = response.json().get("message", "Insufficient balance or out of stock")
                keyboard = [[InlineKeyboardButton("🔙 Back to Countries", callback_data="select_country")]]
                await query.edit_message_text(text=f"❌ নাম্বার কেনা যায়নি!\nকারণ: `{err_msg}`", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error buying number: {e}")
            await query.edit_message_text(text="⚠️ নাম্বার কেনার সময় ত্রুটি ঘটেছে।")

    elif data.startswith("check_sms_"):
        order_id = data.split("_")[2]
        try:
            url = f"https://5sim.net/v1/user/check/{order_id}"
            response = requests.get(url, headers=SIM5_HEADERS, timeout=10)
            
            if response.status_code == 200:
                order_info = response.json()
                status = order_info.get("status")
                sms_list = order_info.get("sms", [])
                
                sms_text = "No SMS received yet. Waiting for OTP..."
                if sms_list:
                    latest_sms = sms_list[-1]
                    sms_text = f"📩 **OTP Code / SMS Text:**\n`{latest_sms.get('text')}`"

                keyboard = [
                    [InlineKeyboardButton("🔄 Refresh SMS", callback_data=f"check_sms_{order_id}")],
                    [InlineKeyboardButton("❌ Cancel Order", callback_data=f"cancel_{order_id}")],
                    [InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]
                ]
                
                msg = f"📦 **Order Status:** `{status}`\n\n{sms_text}"
                await query.edit_message_text(text=msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
            else:
                await query.edit_message_text(text="❌ অর্ডার স্ট্যাটাস চেক করতে সমস্যা হয়েছে।")
        except Exception as e:
            logger.error(f"Error checking SMS: {e}")

    elif data.startswith("cancel_"):
        order_id = data.split("_")[1]
        try:
            url = f"https://5sim.net/v1/user/cancel/{order_id}"
            response = requests.get(url, headers=SIM5_HEADERS, timeout=10)
            
            if response.status_code == 200:
                msg = f"✅ **Order #{order_id} has been cancelled!** আপনার ব্যালেন্স রিফান্ড করা হয়েছে।"
            else:
                msg = f"❌ অর্ডার ক্যানসেল করা সম্ভব হয়নি (সময় শেষ অথবা কোড চলে এসেছে)।"
            
            keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]]
            await query.edit_message_text(text=msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")

    elif data == "check_orders":
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]]
        await query.edit_message_text(text="ℹ️ আপনার শেষ অর্ডারের কোড বা স্ট্যাটাস চেক করতে অর্ডার করার পর পাওয়া পেজ থেকে রিফ্রেশ করুন।", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def main() -> None:
    if not TELEGRAM_BOT_TOKEN or not SIM5_API_TOKEN:
        logger.error("Error: TELEGRAM_BOT_TOKEN বা SIM5_API_TOKEN সেট করা নেই!")
        return

    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))

    logger.info("Bot is starting via Async Loop...")
    
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped manually.")
                
