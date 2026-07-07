import random
import string
import sqlite3

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)


# ==========================
# CONFIG
# ==========================

BOT_TOKEN = "8513193851:AAG_O27OOj3s3lRCruLvgXtA8qxrghscukw"

ADMIN_ID = 8478208834

WALLET = "UQCDRS8uTO3iQV4MTpC9AkT0jBoy9MkOaq2DHUYjNyh7jxhS"



# ==========================
# DATABASE
# ==========================

db = sqlite3.connect(
    "shop.db",
    check_same_thread=False
)

cursor = db.cursor()


cursor.execute("""
CREATE TABLE IF NOT EXISTS orders(

id INTEGER PRIMARY KEY AUTOINCREMENT,

user_id INTEGER,

username TEXT,

plan TEXT,

price TEXT,

port TEXT,

status TEXT

)
""")


db.commit()



# ==========================
# GENERATE PORT
# ==========================

def generate_port():

    chars = (
        string.ascii_letters +
        string.digits
    )

    return "".join(
        random.choice(chars)
        for _ in range(6)
    )



# ==========================
# USER MENU
# ==========================

def plans_menu():

    buttons = [

        [
            InlineKeyboardButton(
                "💎 VIP 7 Days | 2 TON",
                callback_data="plan7"
            )
        ],

        [
            InlineKeyboardButton(
                "🔥 VIP 15 Days | 3.5 TON",
                callback_data="plan15"
            )
        ],

        [
            InlineKeyboardButton(
                "⚡ VIP 30 Days | 5 TON",
                callback_data="plan30"
            )
        ]

    ]

    return InlineKeyboardMarkup(buttons)



# ==========================
# START
# ==========================

async def start(
    update:Update,
    context:ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

"""
💎 <b>Premium Port Service</b>


⚡ سرویس سریع و امن


📦 پلن خود را انتخاب کنید:
""",

        parse_mode="HTML",

        reply_markup=plans_menu()

    )



# ==========================
# PLAN SELECT
# ==========================

async def select_plan(
    update:Update,
    context:ContextTypes.DEFAULT_TYPE
):

    q = update.callback_query

    await q.answer()



    data = {

        "plan7":
        ("VIP 7 Days","2 TON"),

        "plan15":
        ("VIP 15 Days","3.5 TON"),

        "plan30":
        ("VIP 30 Days","5 TON")

    }


    plan,price = data[q.data]


    context.user_data["plan"] = plan
    context.user_data["price"] = price



    keyboard=[

        [

        InlineKeyboardButton(
            "✅ پرداخت کردم",
            callback_data="paid"
        )

        ]

    ]



    await q.edit_message_text(

f"""
💎 <b>Payment Info</b>


📦 سرویس:
<b>{plan}</b>


💰 مبلغ:
<b>{price}</b>


💳 Wallet:

<code>{WALLET}</code>


بعد از پرداخت روی گزینه زیر بزنید.
""",

parse_mode="HTML",

reply_markup=InlineKeyboardMarkup(keyboard)

)

# ==========================
# USER PAYMENT BUTTON
# ==========================

async def paid(
    update:Update,
    context:ContextTypes.DEFAULT_TYPE
):

    q = update.callback_query

    await q.answer()


    user = q.from_user


    plan = context.user_data.get(
        "plan",
        "Unknown"
    )


    price = context.user_data.get(
        "price",
        "Unknown"
    )


    username = (
        user.username
        if user.username
        else "NoUsername"
    )



    cursor.execute(

"""
INSERT INTO orders
(user_id,username,plan,price,port,status)

VALUES (?,?,?,?,?,?)
""",

(
    user.id,
    username,
    plan,
    price,
    "",
    "pending"
)

)

    db.commit()



    order_id = cursor.lastrowid



    await q.edit_message_text(

f"""
✅ <b>سفارش شما ثبت شد</b>


📦 سرویس:
<b>{plan}</b>


💰 مبلغ:
<b>{price}</b>


🆔 شماره سفارش:
<code>{order_id}</code>


⏳ وضعیت:
در انتظار تایید ادمین


🛡️ بعد از بررسی پرداخت، پورت برای شما ارسال می‌شود.
""",

parse_mode="HTML"

)



    admin_keyboard = [

        [

        InlineKeyboardButton(
            "✅ تایید سفارش",
            callback_data=f"accept_{order_id}"
        )

        ],

        [

        InlineKeyboardButton(
            "❌ رد سفارش",
            callback_data=f"reject_{order_id}"
        )

        ]

    ]



    await context.bot.send_message(

        chat_id=ADMIN_ID,

        text=f"""

🚨 <b>سفارش جدید</b>


👤 کاربر:
{user.first_name}


🆔 ID:
<code>{user.id}</code>


🔗 Username:
@{username}


📦 پلن:
<b>{plan}</b>


💰 قیمت:
<b>{price}</b>


🆔 سفارش:
{order_id}

""",

parse_mode="HTML",

reply_markup=InlineKeyboardMarkup(
    admin_keyboard
)

)



# ==========================
# ADMIN PANEL
# ==========================

async def admin_action(
    update:Update,
    context:ContextTypes.DEFAULT_TYPE
):

    q = update.callback_query

    await q.answer()


    if q.from_user.id != ADMIN_ID:

        return



    data = q.data.split("_")


    action = data[0]

    order_id = data[1]



    order = cursor.execute(

"""
SELECT *
FROM orders
WHERE id=?

""",

(order_id,)

).fetchone()



    if not order:

        await q.edit_message_text(
            "❌ سفارش پیدا نشد"
        )

        return



    user_id = order[1]

    plan = order[3]



    # ==================
    # ACCEPT
    # ==================

    if action == "accept":


        port = generate_port()



        cursor.execute(

"""
UPDATE orders

SET port=?,
status=?

WHERE id=?

""",

(
port,
"active",
order_id
)

)

        db.commit()



        await context.bot.send_message(

            chat_id=user_id,


            text=f"""

✅ <b>پرداخت تایید شد</b>


💎 سرویس:
<b>{plan}</b>


🔑 پورت شما:

<code>{port}</code>


⚡ سرویس شما فعال شد.

""",

parse_mode="HTML"

)



        await q.edit_message_text(

f"""
✅ سفارش تایید شد


🆔 سفارش:
{order_id}


🔑 پورت ساخته شد:

<code>{port}</code>
""",

parse_mode="HTML"

)




    # ==================
    # REJECT
    # ==================

    elif action == "reject":


        cursor.execute(

"""
UPDATE orders

SET status=?

WHERE id=?

""",

(
"rejected",
order_id
)

)

        db.commit()



        await context.bot.send_message(

            chat_id=user_id,

            text="""

❌ سفارش شما رد شد.

در صورت اشتباه، با پشتیبانی تماس بگیرید.

"""

        )



        await q.edit_message_text(

f"""

❌ سفارش رد شد


🆔 سفارش:
{order_id}

"""

)





# ==========================
# RUN
# ==========================

def main():

    app = Application.builder().token(
        BOT_TOKEN
    ).build()



    app.add_handler(

        CommandHandler(
            "start",
            start
        )

    )



    app.add_handler(

        CallbackQueryHandler(
            select_plan,
            pattern="^(plan7|plan15|plan30)$"
        )

    )



    app.add_handler(

        CallbackQueryHandler(
            paid,
            pattern="^paid$"
        )

    )



    app.add_handler(

        CallbackQueryHandler(
            admin_action,
            pattern="^(accept|reject)_"
        )

    )



    print("💎 Premium Bot Started")

    app.run_polling()



if __name__ == "__main__":

    main()
