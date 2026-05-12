from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from data.courses import LEVEL_NAMES, EMOJIS

LEVEL_THRESHOLDS = {
    "english": [7, 15, 23, 31],
    "turkish": [4, 11, 19, 24],
    "arabic":  [9, 19, 29, 39],
}


def get_level(score: int, lang: str) -> str:
    names      = LEVEL_NAMES.get(lang, LEVEL_NAMES["english"])
    thresholds = LEVEL_THRESHOLDS.get(lang, [7, 15, 23, 31])
    i = sum(1 for t in thresholds if score > t)
    return f"{EMOJIS[i]} {names[i]}"


def question_kb(q: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{l}) {t}", callback_data=f"ans_{l}")]
        for l, t in q["o"]
    ])
