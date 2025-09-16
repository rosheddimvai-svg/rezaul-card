import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler
from telegram.error import BadRequest

# --- সতর্কতা: এই ডেটা স্থায়ী নয় ---
# বট রিস্টার্ট হলে সমস্ত ডেটা হারিয়ে যাবে।
# এটি শুধুমাত্র দ্রুত পরীক্ষা করার জন্য।
# স্থায়ী সমাধানের জন্য JSON ফাইল ব্যবহার করা উচিত।

# ইন-মেমরি ডেটা স্টোরেজ
user_data = {}
user_agents = [
    {"id": 1, "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36", "status": "available"},
    {"id": 2, "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1", "status": "available"},
    {"id": 3, "user_agent": "Mozilla/5.0 (Linux; Android 10; SM-A205U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.81 Mobile Safari/537.36", "status": "available"}
]

# লগিং সেটআপ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# আপনার ব্যক্তিগত টোকেন এবং আইডি এখানে দিন।
BOT_TOKEN = "7845699149:AAEEKpzHFt5gd6LbApfXSsE8de64f8IaGx0"
ADMIN_CHANNEL_ID = -1002944346537
PUBLIC_CHANNEL_ID = -1003036699455

# --- কমান্ড হ্যান্ডলার ---
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('স্বাগতম! আমি আপনার ইউজার এজেন্ট বট। /help লিখে কমান্ডগুলো দেখতে পারেন।')

def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        """
        কমান্ডসমূহ:
        /mybalance - আপনার বর্তমান ব্যালেন্স দেখুন।
        /topup [টাকা] [ট্রানজ্যাকশন_আইডি] - ব্যালেন্স টপ আপ করার জন্য।
        /buyua - ইউজার এজেন্ট কিনুন।
        /rules - বটের নিয়মাবলী দেখুন।
        """
    )

def rules_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        """
        বট ব্যবহারের নিয়মাবলী:
        - কোনো ভুল ট্রানজ্যাকশন আইডি দিলে টপ আপ হবে না।
        - একবার কেনা ইউজার এজেন্ট আর ফেরত নেওয়া হবে না।
        - সকল প্রকার সমস্যা সমাধানের জন্য সাপোর্ট টিমের সাথে যোগাযোগ করুন।
        """
    )

# --- ব্যালেন্স এবং টপ-আপ ---
def my_balance(update: Update, context: CallbackContext) -> None:
    user_id = str(update.effective_user.id)
    balance = user_data.get(user_id, {}).get('balance', 0)
    update.message.reply_text(f"আপনার বর্তমান ব্যালেন্স: ${balance:.2f}")

def top_up(update: Update, context: CallbackContext) -> None:
    try:
        if len(context.args) < 2:
            update.message.reply_text("ব্যবহারের নিয়ম: /topup [টাকার পরিমাণ] [ট্রানজ্যাকশন আইডি]")
            return
        
        amount = float(context.args[0])
        transaction_id = " ".join(context.args[1:])
        user = update.effective_user
        
        message = (
            f"💰 **নতুন টপ-আপ রিকোয়েস্ট!**\n\n"
            f"**ইউজার আইডি:** `{user.id}`\n"
            f"**ইউজারনেম:** @{user.username or 'N/A'}\n"
            f"**পরিমাণ:** ${amount:.2f}\n"
            f"**ট্রানজ্যাকশন আইডি:** `{transaction_id}`\n\n"
            "আপনি কি এই রিকোয়েস্টটি গ্রহণ করতে চান?"
        )
        
        keyboard = [
            [InlineKeyboardButton("✅ একসেপ্ট", callback_data=f'accept_{user.id}_{amount}'),
             InlineKeyboardButton("❌ রিজেক্ট", callback_data=f'reject_{user.id}')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        context.bot.send_message(
            chat_id=ADMIN_CHANNEL_ID,
            text=message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        update.message.reply_text("আপনার টপ-আপ রিকোয়েস্টটি পাঠানো হয়েছে। দয়া করে অ্যাডমিনের অনুমোদনের জন্য অপেক্ষা করুন।")

    except ValueError:
        update.message.reply_text("টাকার পরিমাণটি ভুল। দয়া করে একটি সংখ্যা দিন।")
    except Exception as e:
        update.message.reply_text(f"একটি সমস্যা হয়েছে: {e}")

# --- ইউজার এজেন্ট লোড এবং সরবরাহ ---
def buy_user_agent(update: Update, context: CallbackContext) -> None:
    price = 10
    user_id = str(update.effective_user.id)
    
    if user_id not in user_data:
        user_data[user_id] = {"balance": 0}

    current_balance = user_data[user_id].get('balance', 0)

    if current_balance < price:
        update.message.reply_text(f"দুঃখিত, আপনার ব্যালেন্স যথেষ্ট নয়। একটি ইউজার এজেন্টের দাম ${price}। আপনার বর্তমান ব্যালেন্স: ${current_balance:.2f}।")
        return

    available_uas = [ua for ua in user_agents if ua.get('status') == 'available']

    if not available_uas:
        update.message.reply_text("দুঃখিত, বর্তমানে কোনো ইউজার এজেন্ট নেই। নতুন স্টকের জন্য অপেক্ষা করুন।")
        return
        
    ua_to_sell = available_uas[0]
    
    # ব্যালেন্স আপডেট করুন
    user_data[user_id]['balance'] -= price
    
    # ইউজার এজেন্ট স্ট্যাটাস আপডেট করুন
    for ua in user_agents:
        if ua.get('id') == ua_to_sell.get('id'):
            ua['status'] = 'sold'
            break

    update.message.reply_text(f"আপনার ইউজার এজেন্টটি:\n\n`{ua_to_sell['user_agent']}`\n\n"
                              f"আপনার নতুন ব্যালেন্স: ${user_data[user_id]['balance']:.2f}")
    
    try:
        context.bot.send_message(
            chat_id=PUBLIC_CHANNEL_ID,
            text=f"🥳 একজন ব্যবহারকারী সফলভাবে একটি ইউজার এজেন্ট কিনেছেন! নতুন স্টক আসছে..."
        )
    except BadRequest:
        logging.error("পাবলিক চ্যানেলে মেসেজ পাঠাতে সমস্যা হয়েছে। নিশ্চিত করুন যে বটটি চ্যানেলের অ্যাডমিন এবং মেসেজ পাঠানোর অনুমতি আছে।")

# --- অ্যাডমিন বাটন হ্যান্ডলার ---
def button_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    
    data = query.data.split('_')
    action = data[0]
    user_id = data[1]

    if action == 'accept':
        amount = float(data[2])
        
        if user_id not in user_data:
            user_data[user_id] = {"balance": 0}
        
        user_data[user_id]['balance'] += amount
        
        try:
            context.bot.send_message(
                chat_id=user_id,
                text=f"✅ আপনার টপ-আপ সফল হয়েছে! আপনার অ্যাকাউন্টে ${amount:.2f} যোগ করা হয়েছে।"
            )
            query.edit_message_text(f"এই রিকোয়েস্টটি গ্রহণ করা হয়েছে।")
        except BadRequest:
            query.edit_message_text("ব্যবহারকারীকে মেসেজ পাঠানো যায়নি।")
            logging.error(f"ইউজার ID {user_id} কে মেসেজ পাঠানো যায়নি।")

    elif action == 'reject':
        try:
            context.bot.send_message(
                chat_id=user_id,
                text=f"❌ দুঃখিত, আপনার টপ-আপ রিকোয়েস্টটি বাতিল করা হয়েছে। কোনো সমস্যা হলে সাপোর্টে যোগাযোগ করুন।"
            )
            query.edit_message_text(f"এই রিকোয়েস্টটি বাতিল করা হয়েছে।")
        except BadRequest:
            query.edit_message_text("ব্যবহারকারীকে মেসেজ পাঠানো যায়নি।")
            logging.error(f"ইউজার ID {user_id} কে মেসেজ পাঠানো যায়নি।")

# --- প্রধান ফাংশন ---
def main() -> None:
    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher

    # কমান্ড হ্যান্ডলার যুক্ত করুন
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("rules", rules_command))
    dispatcher.add_handler(CommandHandler("mybalance", my_balance))
    dispatcher.add_handler(CommandHandler("topup", top_up))
    dispatcher.add_handler(CommandHandler("buyua", buy_user_agent))
    
    # বাটন হ্যান্ডলার যুক্ত করুন
    dispatcher.add_handler(CallbackQueryHandler(button_callback))

    # পোলিং শুরু করুন
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
