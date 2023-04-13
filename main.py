import logging
import os
import sys
import traceback
import asyncio

from flask import Flask, request, render_template
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from utils import download_image_and_convert_to_webp

load_dotenv()

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
ENVIRONMENT = os.getenv("ENVIRONMENT")

ENVIRONMENT_TYPE_DEVELOPMENT = "development"
ENVIRONMENT_TYPE_PRODUCTION = "production"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    greeting = (
        """🇺🇦 Слава Україні 🇺🇦, козаче (берегине)! \n"""
        """Надішли, будь ласка, мені світлину в форматі PNG, "як файл". \n"""
        """Ти можеш скористатись Segment Anything для вирізання об'єктів на фото: https://segment-anything.com/demo"""
    )
    await update.message.reply_text(text=greeting)


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    goodbye = """Бувай, козаче (берегине)! Не забувай донатити на ЗСУ!"""
    await update.message.reply_text(text=goodbye)


async def text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text

    if message_text == "ping":
        await update.message.reply_text("pong")
        return

    reply_text = 'Не бачу картинки - надішли, будь ласка, її "як файл"'
    await update.message.reply_text(reply_text)
    await update.message.reply_text("🙈")


async def photo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_text = 'Надішли, будь ласка, картинку "як файл" - звичайні картинки не зберігають прозорий фон 🤓'
    await update.message.reply_text(reply_text)


async def image_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_text = "Працюю... ⌛"

    wip_message = await update.message.reply_text(reply_text)

    file_id = update.effective_message.document.file_id
    user_file = await context.bot.get_file(file_id)
    file_url = user_file.file_path

    resized_image = download_image_and_convert_to_webp(file_url)

    await context.bot.deleteMessage(chat_id=update.effective_chat.id, message_id=wip_message.message_id)

    await context.bot.send_document(
        chat_id=update.effective_chat.id, document=resized_image, thumb=resized_image, filename="bot_sticker.webp"
    )


async def blacklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    blacklist_reply = """🇺🇦🇺🇦🇺🇦 Слава Україні! 🇺🇦🇺🇦🇺🇦\nТобі тут не раді..."""
    await update.message.reply_text(blacklist_reply)


class BlacklistHandler(MessageHandler):
    def check_update(self, update: Update) -> bool:
        return update.effective_user.language_code in [
            "rus",
            "bel",
            "zho",
            "chi",
            "tir",
        ]


def make_application():
    application = ApplicationBuilder().token(TOKEN).build()

    blacklist_message_hander = BlacklistHandler(filters.ALL, blacklist)
    application.add_handler(blacklist_message_hander)

    text_message_hander = MessageHandler(filters.TEXT & ~filters.COMMAND, text_message)
    application.add_handler(text_message_hander)

    photo_message_filter = (filters.VIDEO | filters.PHOTO | filters.ANIMATION) & ~filters.COMMAND
    photo_message_hander = MessageHandler(photo_message_filter, photo_message)
    application.add_handler(photo_message_hander)

    image_document_message_handler = MessageHandler(filters.Document.IMAGE & ~filters.COMMAND, image_document)
    application.add_handler(image_document_message_handler)

    start_handler = CommandHandler("start", start)
    application.add_handler(start_handler)

    stop_handler = CommandHandler("stop", stop)
    application.add_handler(stop_handler)

    return application


bot_application = make_application()
application = Flask(__name__)

if ENVIRONMENT == ENVIRONMENT_TYPE_PRODUCTION:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    asyncio.run
    logger.info("Set webhook")
    loop.run_until_complete(
        bot_application.bot.set_webhook(
            url=WEBHOOK_URL,
        )
    )
    loop.run_until_complete(bot_application.initialize())
    loop.run_until_complete(bot_application.start())


@application.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot_application.bot)
        response = None
        try:
            loop = asyncio.get_event_loop()
            response = loop.run_until_complete(bot_application.process_update(update))
        except Exception as e:
            print(traceback.format_exc())

        return "OK"

    return render_template("index.html")


def main():
    if ENVIRONMENT == ENVIRONMENT_TYPE_DEVELOPMENT:
        print("Starting development server")
        bot_application.run_polling()
    else:
        print("You should use bot_application wrappers (like Flask) in production ")
        application.run(port="5005")


if __name__ == "__main__":
    main()
