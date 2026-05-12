from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from storage import STORAGE
from keyboards import CONTACT_KB, MAIN_KB
from subscription import check_and_notify


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await check_and_notify(update, context):
        return
    context.user_data.clear()
    await update.message.reply_text(
        "👋 <b>Career Center botiga xush kelibsiz!</b>\n\n"
        "Davom etish uchun telefon raqamingizni ulashing 👇",
        parse_mode="HTML", reply_markup=CONTACT_KB,
    )


async def on_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await check_and_notify(update, context):
        return
    contact  = update.message.contact
    user     = update.effective_user
    name     = user.full_name or user.first_name
    phone    = contact.phone_number
    username = f"@{user.username}" if user.username else "—"

    context.user_data.update({
        "phone": phone, "name": name,
        "user_id": user.id, "username": username,
    })
    STORAGE["users"][user.id] = {
        "name": name, "phone": phone, "username": username,
        "joined": datetime.now().strftime("%d.%m.%Y %H:%M"),
    }
    await update.message.reply_text(
        f"✅ <b>Ro'yxatdan o'tdingiz!</b>\n\nXush kelibsiz, <b>{user.first_name}</b>! 👋\n\n"
        "Quyidagi bo'limlardan birini tanlang 👇",
        parse_mode="HTML", reply_markup=MAIN_KB,
    )
