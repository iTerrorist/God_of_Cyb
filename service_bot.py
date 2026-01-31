import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)
from db import is_allowed, save_report

# توکن و آیدی‌ها که داخل متغیرهای محیطی تنظیم می‌کنید (Render)
TOKEN = os.getenv("8406194824:AAHqdcH6ap1zuQtFEAOE5P0XuCpk2lrmeWE")  # توکن بات اصلی
ADMIN_GROUP = int(os.getenv("-5222161431"))  # آیدی گپ

state = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_allowed(uid):
        await update.message.reply_text("❗️شما اشتراک فعال ندارید")
        return

    kb = [
        [InlineKeyboardButton("اکانت", callback_data="اکانت")],
        [InlineKeyboardButton("چنل", callback_data="چنل")],
        [InlineKeyboardButton("گپ", callback_data="گپ")]
    ]

    await update.message.reply_text(
        "سلام ، به ربات خدمات devex-i خوش آمدی.\n"
        "لطفا از منوی زیر یک گزینه را انتخاب کنید",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def choose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    state[q.from_user.id] = {"type": q.data, "step": "id"}
    await q.edit_message_text("🆔 لطفا آیدی را ارسال کنید")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in state:
        return

    s = state[uid]

    if s["step"] == "id":
        s["target"] = update.message.text
        s["step"] = "reason"
        await update.message.reply_text("⚠️ نوع تخلف را ارسال کنید")
    elif s["step"] == "reason":
        s["reason"] = update.message.text
        s["step"] = "image"
        await update.message.reply_text("📸 عکس بفرستید یا /skip")

async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in state:
        return
    s = state[uid]
    photo_id = update.message.photo[-1].file_id

    save_report(uid, s["target"], s["type"], s["reason"], photo_id)

    await context.bot.send_photo(
        ADMIN_GROUP,
        photo_id,
        caption=(
            "📨 گزارش جدید\n\n"
            f"📌 نوع: {s['type']}\n"
            f"🆔 آیدی: {s['target']}\n"
            f"⚠️ تخلف: {s['reason']}\n"
            f"👤 کاربر: {uid}"
        )
    )

    await update.message.reply_text("موفق ✅ - لطفا منتظر باشید\n\ndevex-i")
    del state[uid]

async def skip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in state:
        return
    s = state[uid]
    save_report(uid, s["target"], s["type"], s["reason"])

    await context.bot.send_message(
        ADMIN_GROUP,
        "📨 گزارش جدید\n\n"
        f"📌 نوع: {s['type']}\n"
        f"🆔 آیدی: {s['target']}\n"
        f"⚠️ تخلف: {s['reason']}\n"
        f"👤 کاربر: {uid}"
    )

    await update.message.reply_text("موفق ✅ - لطفا منتظر باشید\n\ndevex-i")
    del state[uid]

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(choose))
app.add_handler(CommandHandler("skip", skip))
app.add_handler(MessageHandler(filters.PHOTO, photo))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

print("Service bot ready")
app.run_polling()
