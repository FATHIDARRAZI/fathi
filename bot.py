import logging
import json
import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# API settings
API_URL = "https://bestsmmprovider.com/api/v2"
API_KEY = "6531b4d73b0d5c6ade83e71ee1a0cb88"

# Admin settings
ADMIN_ID = 1108165567
SUPER_USER_ID = 1108165567

# User database file
USER_DB_FILE = "users_db.json"

# Service data
services = {
    "1192": {
        "name": "إعجابات إنستغرام - ارخص خدمة",
        "desc": "وقت البدء: البدء الفوري\nنوع الحسابات: جودة جيدة\nزر إعادة التعبئة لمدة عام",
        "min": 10,
        "max": 300000,
        "price_per_1000": 0.5462
    },
    "2235": {
        "name": "مشاهدات انستغرام | 200 ألف يوميا 🚀",
        "desc": "⌛ وقت البدء المتوقع: فوري\n⚡ متوسط ‌السرعة: 200 ألف يوميًا\n💎 الجودة: مستخدمون حقيقيون",
        "min": 100,
        "max": 200000,
        "price_per_1000": 0.1282
    }
}

# Load or initialize user data
if os.path.exists(USER_DB_FILE):
    with open(USER_DB_FILE, "r") as f:
        user_data = json.load(f)
else:
    user_data = {}

def save_user_data():
    with open(USER_DB_FILE, "w") as f:
        json.dump(user_data, f)

def is_admin(update: Update):
    return update.effective_user.id == ADMIN_ID

def is_super_user(update: Update):
    return update.effective_user.id == SUPER_USER_ID

# === Commands ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(service["name"], callback_data=service_id)] for service_id, service in services.items()]
    await update.message.reply_text("مرحباً 👋 اختر الخدمة عبر الضغط على الزر المناسب:", reply_markup=InlineKeyboardMarkup(keyboard))

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    username = update.message.text.split(" ", 1)[1] if len(update.message.text.split(" ", 1)) > 1 else None
    if not username:
        await update.message.reply_text("❌ أدخل اسم المستخدم: `/register your_username`", parse_mode='Markdown')
        return
    if user_id in user_data:
        await update.message.reply_text("🚫 لديك حساب بالفعل!")
        return
    user_data[user_id] = {"username": username, "balance": 0, "banned": False}
    save_user_data()
    await update.message.reply_text(f"✅ تم تسجيلك بنجاح! اسم المستخدم: {username}")

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if user_id in user_data:
        await update.message.reply_text(f"💰 رصيدك الحالي هو: {user_data[user_id]['balance']} درهم")
    else:
        await update.message.reply_text("❌ لم يتم تسجيلك بعد. استخدم /register لتسجيل حسابك.")

async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🆔 معرفك هو: `{update.effective_user.id}`", parse_mode="Markdown")

# === Admin Commands ===

async def all_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_super_user(update):
        await update.message.reply_text("🚫 هذا الأمر مخصص للمستخدم الفائق فقط.")
        return
    if not user_data:
        await update.message.reply_text("📭 لا يوجد مستخدمون.")
        return
    users_info = "\n".join([
        f"🆔 {uid} | 👤 {data['username']} | 💰 {data['balance']} | ✅​ {'محظور' if data.get('banned') else 'نشط'}"
        for uid, data in user_data.items()
    ])
    await update.message.reply_text(f"📜 قائمة المستخدمين:\n{users_info}")

async def add_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("🚫 هذا الأمر للأدمن فقط.")
        return
    args = context.args
    if len(args) != 2:
        await update.message.reply_text("❌ أدخل ID أو اسم المستخدم والمبلغ. مثال: /add_balance 123456 50")
        return
    user_id_or_username, amount = args
    user_id = next((uid for uid, data in user_data.items()
                    if data["username"] == user_id_or_username or uid == user_id_or_username), None)
    if user_id:
        user_data[user_id]["balance"] += int(amount)
        save_user_data()
        await update.message.reply_text(f"✅ تم إضافة {amount} درهم للمستخدم {user_data[user_id]['username']}.")
    else:
        await update.message.reply_text("❌ المستخدم غير موجود.")

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("🚫 هذا الأمر للأدمن فقط.")
        return
    args = context.args
    if not args:
        await update.message.reply_text("❌ استخدم الأمر مع ID أو اسم المستخدم. مثال: /ban 123456")
        return
    target = args[0]
    user_id = next((uid for uid, data in user_data.items()
                    if data["username"] == target or uid == target), None)
    if user_id:
        user_data[user_id]["banned"] = True
        save_user_data()
        await update.message.reply_text(f"🚫 تم حظر المستخدم: {user_data[user_id]['username']}")
    else:
        await update.message.reply_text("❌ المستخدم غير موجود.")

async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("🚫 هذا الأمر للأدمن فقط.")
        return
    args = context.args
    if not args:
        await update.message.reply_text("❌ استخدم الأمر مع ID أو اسم المستخدم. مثال: /unban 123456")
        return
    target = args[0]
    user_id = next((uid for uid, data in user_data.items()
                    if data["username"] == target or uid == target), None)
    if user_id:
        user_data[user_id]["banned"] = False
        save_user_data()
        await update.message.reply_text(f"✅ تم رفع الحظر عن المستخدم: {user_data[user_id]['username']}")
    else:
        await update.message.reply_text("❌ المستخدم غير موجود.")
        

# === Order Flow ===

async def service_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    if user_id not in user_data:
        await query.message.reply_text("🚫 يجب عليك التسجيل أولاً عبر /register قبل تقديم أي طلب.")
        return
    if user_data[user_id].get("banned"):
        await query.message.reply_text("🚫 لقد تم حظرك من استخدام البوت.")
        return

    service_id = query.data
    service = services[service_id]
    context.user_data["pending_order"] = {"service_id": service_id}

    message = f"""📌 *{service['name']}*\n{service['desc']}\n💰 السعر: {service['price_per_1000']} درهم لكل 1000\n🔢 أقل كمية: {service['min']} - أقصى كمية: {service['max']}\n\n📝 أرسل *الرابط* الآن 👇"""
    await query.message.reply_text(message, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if user_id not in user_data:
        await update.message.reply_text("❌ يجب عليك التسجيل أولاً.")
        return
    if user_data[user_id].get("banned"):
        await update.message.reply_text("🚫 لقد تم حظرك من استخدام البوت.")
        return

    pending_order = context.user_data.get("pending_order")
    if not pending_order:
        await update.message.reply_text("❗ اختر الخدمة أولاً باستخدام /start.")
        return

    if "link" not in pending_order:
        pending_order["link"] = update.message.text
        await update.message.reply_text("📦 الآن أدخل *الكمية* التي تريدها:", parse_mode='Markdown')
    else:
        try:
            quantity = int(update.message.text)
        except ValueError:
            await update.message.reply_text("❌ من فضلك أدخل رقم صالح.")
            return

        service_id = pending_order["service_id"]
        service = services[service_id]

        if quantity < service["min"] or quantity > service["max"]:
            await update.message.reply_text(f"❌ الكمية يجب أن تكون بين {service['min']} و {service['max']}")
            return

        cost = (quantity / 1000) * service["price_per_1000"]
        balance = user_data[user_id]["balance"]

        if balance < cost:
            await update.message.reply_text(f"❌ رصيدك غير كافٍ. الكلفة: {cost:.2f} درهم، رصيدك: {balance} درهم")
            return

        # إرسال الطلب إلى المزود
        response = requests.post(API_URL, data={
            "key": API_KEY,
            "action": "add",
            "service": service_id,
            "link": pending_order["link"],
            "quantity": quantity
        })

        result = response.json()

        if "order" in result:
            user_data[user_id]["balance"] -= cost
            save_user_data()
            await update.message.reply_text(f"✅ تم تنفيذ الطلب بنجاح!\nرقم الطلب: {result['order']}\n💰 تم خصم: {cost:.2f} درهم")
            context.user_data["pending_order"] = None
        else:
            await update.message.reply_text(f"❌ فشل تنفيذ الطلب: {result}")
            context.user_data["pending_order"] = None

# === Help ===

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""
🆘 *مساعدة*:
/start - عرض قائمة الخدمات 📌
/register <username> - تسجيل مستخدم جديد ✍️
/myid - معرف المستخدم 🆔
/balance - معرفة الرصيد 💰
/add_balance <id|username> <amount> - إضافة رصيد ➕ (أدمن)
/all_users - عرض جميع المستخدمين 🧾 (سوبر يوزر)
/ban <id|username> - حظر مستخدم 🚫 (أدمن)
/unban <id|username> - إلغاء الحظر ✅ (أدمن)
""", parse_mode="Markdown")

# === Run Bot ===

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token("7755256026:AAEEoaJwOaP1gkff_yVWoW4VFFOWPZ4HKDk").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("register", register))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("all_users", all_users))
    app.add_handler(CommandHandler("add_balance", add_balance))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(CallbackQueryHandler(service_selected))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()
