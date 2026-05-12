import sys
import logging

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

from telegram import Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters,
)
from telegram.request import HTTPXRequest
from config import TOKEN
from handlers.start import cmd_start, on_contact
from handlers.text import on_text
from handlers.callback import on_callback
from handlers.admin import cmd_admin

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.WARNING,
)


async def error_handler(update: object, context) -> None:
    import telegram.error as tgerr
    if isinstance(context.error, (tgerr.TimedOut, tgerr.NetworkError)):
        return
    logging.error("Xato:", exc_info=context.error)


def main() -> None:
    request = HTTPXRequest(
        connect_timeout=60,
        read_timeout=60,
        write_timeout=60,
        pool_timeout=60,
    )
    app = Application.builder().token(TOKEN).request(request).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(MessageHandler(filters.CONTACT, on_contact))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.add_error_handler(error_handler)

    print("✅ Bot ishga tushdi! Telegram'da /start bosing.")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
        timeout=30,
    )


if __name__ == "__main__":
    main()
