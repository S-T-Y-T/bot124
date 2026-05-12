import logging
from telegram import Update
from telegram.ext import ContextTypes
from config import MANAGER_ID
from keyboards import CONTACT_KB, COURSE_LANG_KB, TEST_LANG_KB
from data.courses import LANG_LABEL
from subscription import check_and_notify


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await check_and_notify(update, context):
        return

    text = update.message.text

    if not context.user_data.get("phone"):
        await update.message.reply_text(
            "Iltimos, avval telefon raqamingizni ulashing 👇",
            reply_markup=CONTACT_KB,
        )
        return

    if text == "💬 Career Center haqida fikr bildirish":
        context.user_data["state"] = "awaiting_feedback"
        await update.message.reply_text(
            "✍️ <b>Fikringizni yozing!</b>\n\n"
            "Career Center haqidagi fikr-mulohazalaringizni yozing.\n"
            "Rahbarimizga avtomatik yuboriladi. 📩",
            parse_mode="HTML",
        )
        return

    if text == "📖 Kurslarimiz haqida ma'lumot":
        await update.message.reply_text(
            "📖 <b>Qaysi til kurslari haqida ma'lumot olmoqchisiz?</b>",
            parse_mode="HTML", reply_markup=COURSE_LANG_KB,
        )
        return

    if text == "📝 Placement Test":
        await update.message.reply_text(
            "📝 <b>Qaysi til bo'yicha test topshirmoqchisiz?</b>",
            parse_mode="HTML", reply_markup=TEST_LANG_KB,
        )
        return

    if context.user_data.get("state") == "awaiting_feedback":
        context.user_data["state"] = None
        lang      = context.user_data.get("test_lang")
        lang_name = LANG_LABEL.get(lang, "Test topshirilmagan")
        level     = context.user_data.get("result_level", "—")
        score     = context.user_data.get("result_score", "—")
        total     = context.user_data.get("result_total", "—")

        msg = (
            "📝 <b>Yangi fikr-mulohaza!</b>\n\n"
            f"👤 {context.user_data.get('name','?')} ({context.user_data.get('username','?')})\n"
            f"🆔 <code>{context.user_data.get('user_id','?')}</code>\n"
            f"📞 {context.user_data.get('phone','?')}\n"
            f"🌐 Test tili: {lang_name}\n"
            f"📊 Natija: {score}/{total} — {level}\n\n"
            f"💬 <b>Fikr:</b>\n{text}"
        )
        try:
            await context.bot.send_message(chat_id=MANAGER_ID, text=msg, parse_mode="HTML")
            await update.message.reply_text(
                "✅ <b>Rahmat!</b> Fikringiz rahbarimizga yuborildi. 🙏",
                parse_mode="HTML",
            )
        except Exception as e:
            logging.warning(f"Manager xato: {e}")
            await update.message.reply_text("⚠️ Xabar yuborishda xatolik yuz berdi.")
