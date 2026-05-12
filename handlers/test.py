from datetime import datetime
from telegram.ext import ContextTypes
from data.questions import ALL_QUESTIONS
from data.courses import LANG_LABEL
from storage import STORAGE
from utils import get_level, question_kb
from keyboards import result_kb


async def send_q(msg, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = context.user_data["test_lang"]
    idx  = context.user_data["current"]
    qs   = ALL_QUESTIONS[lang]

    if idx >= len(qs):
        await show_result(msg, context)
        return

    q      = qs[idx]
    header = f"<b>{q['lv']}</b>  |  {idx + 1}/{len(qs)}\n\n{q['q']}"
    await msg.reply_text(header, reply_markup=question_kb(q), parse_mode="HTML")


async def process_ans(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = context.user_data["test_lang"]
    idx  = context.user_data["current"]
    qs   = ALL_QUESTIONS[lang]

    if idx >= len(qs):
        return

    q          = qs[idx]
    user_ans   = query.data.split("_")[1]
    correct    = q["a"]

    if user_ans == correct:
        context.user_data["score"] += 1
        mark = "✅"
    else:
        ct   = next(t for l, t in q["o"] if l == correct)
        mark = f"❌  To'g'ri: <b>{correct}) {ct}</b>"

    try:
        await query.edit_message_text(f"{q['q']}\n\n{mark}", parse_mode="HTML")
    except Exception:
        pass

    context.user_data["current"] = idx + 1
    await send_q(query.message, context)


async def show_result(msg, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang      = context.user_data["test_lang"]
    score     = context.user_data["score"]
    total     = len(ALL_QUESTIONS[lang])
    level     = get_level(score, lang)
    lang_name = LANG_LABEL[lang]

    context.user_data.update({
        "result_level": level, "result_score": score,
        "result_total": total, "state": None,
    })
    STORAGE["results"].append({
        "name":     context.user_data.get("name", "?"),
        "phone":    context.user_data.get("phone", "?"),
        "username": context.user_data.get("username", "—"),
        "lang":     lang_name, "score": score, "total": total,
        "level":    level, "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
    })

    text = (
        f"🎉 <b>Tabriklaymiz!</b> Siz {lang_name} placement testni muvafaqiyatli topshirdingiz!\n\n"
        f"📊 <b>Sizning darajangiz:</b> {level}\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Endi siz bilimingizni yanada mustahkamlash vaqti keldi!\n\n"
        "🏆 <b>CAREER CENTER</b> bilan guruhlarga hoziroq qo'shiling va bonuslarga ega bo'ling! 🎁"
    )
    await msg.reply_text(text, parse_mode="HTML", reply_markup=result_kb())
