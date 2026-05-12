from telegram import Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes
from config import REQUIRED_CHANNEL

_SUB_MSG = (
    "📢 <b>Botdan foydalanish uchun kanalimizga obuna bo'ling!</b>\n\n"
    f"Kanal: {REQUIRED_CHANNEL}\n\n"
    "Obuna bo'lgach «✅ Obunani tekshirish» tugmasini bosing 👇"
)


async def is_subscribed(user_id: int, bot) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
        return member.status in ("member", "administrator", "creator")
    except TelegramError:
        return True  # kanal topilmasa yoki xato bo'lsa — ruxsat beramiz


async def check_and_notify(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Returns True if subscribed. If not — sends a subscription prompt and returns False."""
    from keyboards import subscription_kb

    user_id = update.effective_user.id
    if await is_subscribed(user_id, context.bot):
        return True

    if update.message:
        await update.message.reply_text(
            _SUB_MSG, parse_mode="HTML", reply_markup=subscription_kb(),
        )
    elif update.callback_query:
        await update.callback_query.answer(
            "Iltimos, avval kanalga obuna bo'ling!", show_alert=True,
        )
        await update.callback_query.message.reply_text(
            _SUB_MSG, parse_mode="HTML", reply_markup=subscription_kb(),
        )
    return False
