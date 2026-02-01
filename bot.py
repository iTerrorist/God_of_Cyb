import time
import random
from urllib.parse import quote
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

TOKEN = "8406194824:AAHqdcH6ap1zuQtFEAOE5P0XuCpk2lrmeWE"
ADMIN_GROUP = "-1001234567890"

state = {}
users = {}
used_test = set()
report_count = {}
trust_score = {}
targets = {}

CODES = {
    "Devexi-test": "test",
    "Deopi2nsA11": "month",
    "Upojwj11": "year"
}

# ----------------------------

def is_allowed(uid):
    return uid in users and users[uid] > time.time()

def build_spambot_link(text):
    return "https://t.me/spambot?start=" + quote(text)

# --- Subscription Logic ---

def extend_expire(current_ts, code):
    now = datetime.now()
    base = datetime.fromtimestamp(current_ts) if current_ts and current_ts > time.time() else now

    if code == "test":
        return base + timedelta(days=1)

    if code == "month":
        try:
            return base.replace(month=base.month + 1)
        except:
            return base + timedelta(days=30)

    if code == "year":
        try:
            return base.replace(year=base.year + 1)
        except:
            return base + timedelta(days=365)

# ----------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if not is_allowed(uid):
        state[uid] = {"step": "code"}
        await update.message.reply_text("🔐 لطفا کد اشتراک را ارسال کنید:")
        return

    await show_menu(update)

# ----------------------------

async def show_menu(update):
    kb = [
        [InlineKeyboardButton("🧊 Scam", callback_data="Scam")],
        [InlineKeyboardButton("🧊 Impersonation", callback_data="Impersonation")],
        [InlineKeyboardButton("🧊 NSFW", callback_data="NSFW")],
        [InlineKeyboardButton("🧊 Terrorism", callback_data="Terrorism")],
        [InlineKeyboardButton("🧊 Drugs", callback_data="Drugs")],
        [InlineKeyboardButton("🧊 Spam", callback_data="Spam")],
        [InlineKeyboardButton("🧊 Other", callback_data="Other")]
    ]

    await update.message.reply_text(
        "🛡 Devex-i Report Center\n\nSelect violation:",
        reply_markup=InlineKeyboardMarkup(kb)
    )

# ----------------------------

async def choose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id
    await q.answer()

    if not is_allowed(uid):
        await q.edit_message_text("❌ اشتراک منقضی شده. /start بزن")
        return

    state[uid] = {"type": q.data, "step": "id"}
    await q.edit_message_text("🆔 آیدی یا لینک هدف را بفرست:")

# ----------------------------

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()

    # ---- Enter Subscription Code ----
    if uid in state and state[uid].get("step") == "code":
        if text not in CODES:
            await update.message.reply_text("❌ کد اشتباه است")
            return

        if text == "Devexi-test" and uid in used_test:
            await update.message.reply_text("❌ تست قبلاً استفاده شده")
            return

        current = users.get(uid, 0)
        new_expire = extend_expire(current, CODES[text])
        users[uid] = new_expire.timestamp()

        if text == "Devexi-test":
            used_test.add(uid)

        del state[uid]
        await update.message.reply_text(
            f"✅ اشتراک فعال شد\n"
            f"⏳ اعتبار تا: {new_expire.strftime('%Y-%m-%d %H:%M')}\n\n"
            "/start"
        )
        return

    if uid not in state:
        return

    s = state[uid]

    # ---- Anti-Spam ----
    now = time.time()
    report_count.setdefault(uid, [])
    report_count[uid] = [t for t in report_count[uid] if now - t < 3600]
    if len(report_count[uid]) >= 3:
        await update.message.reply_text("🚫 بیش از حد گزارش داده‌اید")
        return

    # ---- Reporting Flow ----
    if s["step"] == "id":
        s["target"] = text
        s["step"] = "reason"
        await update.message.reply_text("📝 توضیح تخلف را بنویس:")

    elif s["step"] == "reason":
        s["reason"] = text
        await update.message.reply_text("📡 گزارش در حال ارسال... لطفا منتظر باشید")

        # Threat level
        risk = "Low"
        for w in ["terror", "bomb", "isis", "child", "rape", "drug", "fraud"]:
            if w in text.lower():
                risk = "Critical"
                break

        # Ticket & trust
        ticket = f"DX-{random.randint(10000,99999)}"
        trust_score[uid] = trust_score.get(uid, 0) + 1
        report_count[uid].append(now)

        # Target counter
        targets[s["target"]] = targets.get(s["target"], 0) + 1
        count = targets[s["target"]]

        # SpamBot packet
        packet = (
            f"Abuse Report\n\n"
            f"Target: {s['target']}\n"
            f"Category: {s['type']}\n"
            f"Description: {s['reason']}\n"
            f"Reports: {count}\n"
            f"Case: {ticket}"
        )

        spambot = build_spambot_link(packet)

        await context.bot.send_message(
            ADMIN_GROUP,
            "🚨 Devex-i Abuse Case\n\n"
            f"🎫 {ticket}\n"
            f"⚠️ {risk}\n"
            f"🎯 {s['target']}\n"
            f"📊 Reports: {count}\n"
            f"📂 {s['type']}\n"
            f"📝 {s['reason']}\n\n"
            f"📨 Send to Telegram:\n{spambot}"
        )

        await update.message.reply_text(f"✅ ارسال شد\nTicket: {ticket}")
        del state[uid]

# ----------------------------

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(choose))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

print("Devex-i running…")
app.run_polling()
