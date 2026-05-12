from telegram import (
    KeyboardButton, ReplyKeyboardMarkup,
    InlineKeyboardButton, InlineKeyboardMarkup,
)
from config import ADMIN_LINK, REQUIRED_CHANNEL

CONTACT_KB = ReplyKeyboardMarkup(
    [[KeyboardButton("📱 Telefon raqamimni ulashish", request_contact=True)]],
    resize_keyboard=True, one_time_keyboard=True,
)

MAIN_KB = ReplyKeyboardMarkup(
    [
        ["💬 Career Center haqida fikr bildirish"],
        ["📖 Kurslarimiz haqida ma'lumot", "📝 Placement Test"],
    ],
    resize_keyboard=True,
)

COURSE_LANG_KB = InlineKeyboardMarkup([
    [InlineKeyboardButton("🇸🇦 Arab tili",   callback_data="course_arabic")],
    [InlineKeyboardButton("🇬🇧 Ingliz tili", callback_data="course_english")],
    [InlineKeyboardButton("🇹🇷 Turk tili",   callback_data="course_turkish")],
])

TEST_LANG_KB = InlineKeyboardMarkup([
    [InlineKeyboardButton("🇸🇦 Arab tili",   callback_data="test_arabic")],
    [InlineKeyboardButton("🇬🇧 Ingliz tili", callback_data="test_english")],
    [InlineKeyboardButton("🇹🇷 Turk tili",   callback_data="test_turkish")],
])


def result_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 Kursga yoziling",          callback_data="enroll_course")],
        [InlineKeyboardButton("👨‍💼 Admin bilan bog'lanish", url=ADMIN_LINK)],
    ])


def subscription_kb() -> InlineKeyboardMarkup:
    channel_url = f"https://t.me/{REQUIRED_CHANNEL.lstrip('@')}"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Kanalga obuna bo'lish", url=channel_url)],
        [InlineKeyboardButton("✅ Obunani tekshirish",    callback_data="check_sub")],
    ])
