from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import MANAGER_ID
from storage import STORAGE

ADMIN_MAIN_KB = InlineKeyboardMarkup([
    [InlineKeyboardButton("👥 Foydalanuvchilar",   callback_data="adm_users"),
     InlineKeyboardButton("📊 Test natijalari",    callback_data="adm_results")],
    [InlineKeyboardButton("✅ Kursga yozilganlar", callback_data="adm_enrolled")],
])


async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if str(update.effective_user.id) != MANAGER_ID:
        return
    u = len(STORAGE["users"])
    r = len(STORAGE["results"])
    e = len(STORAGE["enrolled"])
    await update.message.reply_text(
        "🔐 <b>ADMIN PANEL</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{u}</b>\n"
        f"📝 Placement test yechganlar: <b>{r}</b>\n"
        f"✅ Kursga yozilganlar: <b>{e}</b>",
        parse_mode="HTML", reply_markup=ADMIN_MAIN_KB,
    )


async def handle_admin_cb(query, data: str) -> None:
    if data == "adm_users":
        items = list(STORAGE["users"].values())
        if not items:
            await query.message.reply_text("Hali foydalanuvchilar yo'q.")
            return
        lines = [
            f"{i}. {u['name']} | {u['phone']} | {u['username']} | {u['joined']}"
            for i, u in enumerate(items[-30:], 1)
        ]
        await query.message.reply_text(
            f"👥 <b>Foydalanuvchilar ({len(items)} ta):</b>\n\n" + "\n".join(lines),
            parse_mode="HTML",
        )

    elif data == "adm_results":
        items = STORAGE["results"]
        if not items:
            await query.message.reply_text("Hali test natijalari yo'q.")
            return
        lines = [
            f"{i}. {r['name']} | {r['phone']}\n"
            f"   {r['lang']} | {r['score']}/{r['total']} | {r['level']}\n"
            f"   📅 {r['date']}"
            for i, r in enumerate(items[-20:], 1)
        ]
        await query.message.reply_text(
            f"📊 <b>Test natijalari ({len(items)} ta):</b>\n\n" + "\n\n".join(lines),
            parse_mode="HTML",
        )

    elif data == "adm_enrolled":
        items = STORAGE["enrolled"]
        if not items:
            await query.message.reply_text("Hali kursga yozilganlar yo'q.")
            return
        lines = [
            f"{i}. {e['name']} | {e['phone']}\n"
            f"   {e['lang']} | {e['level']}\n"
            f"   📅 {e['date']}"
            for i, e in enumerate(items[-20:], 1)
        ]
        await query.message.reply_text(
            f"✅ <b>Kursga yozilganlar ({len(items)} ta):</b>\n\n" + "\n\n".join(lines),
            parse_mode="HTML",
        )
