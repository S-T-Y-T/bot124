from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from config import MANAGER_ID, RECEPTION_LINK
from data.courses import COURSE_INFO, TEST_INTRO, LANG_LABEL
from storage import STORAGE
from keyboards import CONTACT_KB, MAIN_KB, subscription_kb
from subscription import is_subscribed
from handlers.test import send_q, process_ans
from handlers.admin import handle_admin_cb

_SUB_PROMPT = (
    "📢 <b>Botdan foydalanish uchun kanalimizga obuna bo'ling!</b>\n\n"
    "Obuna bo'lgach «✅ Obunani tekshirish» tugmasini bosing 👇"
)


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data  = query.data

    # ── Obuna tekshirish ──────────────────────────────────────────
    if data == "check_sub":
        if await is_subscribed(query.from_user.id, context.bot):
            if context.user_data.get("phone"):
                await query.message.reply_text(
                    "✅ <b>Ajoyib!</b> Obuna tasdiqlandi! Quyidagi bo'limlardan birini tanlang 👇",
                    parse_mode="HTML", reply_markup=MAIN_KB,
                )
            else:
                await query.message.reply_text(
                    "✅ <b>Ajoyib!</b> Obuna tasdiqlandi!\n\n"
                    "Davom etish uchun telefon raqamingizni ulashing 👇",
                    parse_mode="HTML", reply_markup=CONTACT_KB,
                )
        else:
            await query.answer("Siz hali kanalga obuna bo'lmagansiz!", show_alert=True)
        return

    # ── Admin callbacklar uchun obuna tekshirilmaydi ──────────────
    if not data.startswith("adm_"):
        if not await is_subscribed(query.from_user.id, context.bot):
            await query.answer("Iltimos, avval kanalga obuna bo'ling!", show_alert=True)
            await query.message.reply_text(
                _SUB_PROMPT, parse_mode="HTML", reply_markup=subscription_kb(),
            )
            return

    # ── Kurs ma'lumotlari ─────────────────────────────────────────
    if data.startswith("course_"):
        lang = data[7:]
        await query.message.reply_text(COURSE_INFO[lang], parse_mode="HTML")
        return

    # ── Test boshlash ─────────────────────────────────────────────
    if data.startswith("test_"):
        lang = data[5:]
        context.user_data.update({
            "test_lang": lang, "score": 0,
            "current": 0, "answers": [],
            "state": "in_test",
        })
        await query.message.reply_text(TEST_INTRO[lang], parse_mode="HTML")
        await send_q(query.message, context)
        return

    # ── Javob qayta ishlash ───────────────────────────────────────
    if data.startswith("ans_"):
        if context.user_data.get("state") != "in_test":
            return
        await process_ans(query, context)
        return

    # ── Kursga yozilish ───────────────────────────────────────────
    if data == "enroll_course":
        lang_name = LANG_LABEL.get(context.user_data.get("test_lang", ""), "")
        level     = context.user_data.get("result_level", "—")
        STORAGE["enrolled"].append({
            "name":     context.user_data.get("name", "?"),
            "phone":    context.user_data.get("phone", "?"),
            "username": context.user_data.get("username", "—"),
            "lang":     lang_name, "level": level,
            "date":     datetime.now().strftime("%d.%m.%Y %H:%M"),
        })
        await query.message.reply_text(
            "✅ <b>Zo'r!</b> Ma'lumotlaringiz qabul qilindi.\n\n"
            f"Reception bilan bog'laning: {RECEPTION_LINK}",
            parse_mode="HTML",
        )
        return

    # ── Admin callbacklar ─────────────────────────────────────────
    if data.startswith("adm_"):
        if str(query.from_user.id) != MANAGER_ID:
            return
        await handle_admin_cb(query, data)
        return
