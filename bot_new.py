#!/bin/env python3

# Imports
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler
from config import config

# Initialize logging module
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Implements /start command"""
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="ברוכים הבאים לבוט של גורדי ויובי")


def main():
    app = ApplicationBuilder().token(config["token"]).build()
    start_handler = CommandHandler('start', start)
    app.add_handler(start_handler)
    app.run_polling()


if __name__ == '__main__':
    main()
