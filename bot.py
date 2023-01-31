#!/bin/env python3

# Imports
import logging
from telegram import Update
from telegram.ext import filters, ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler
from config import config
import pandas as pd
from thefuzz import process, fuzz

# Initialize logging module
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


# Decorator function requiring admin access to a handle
def admin_required(func):
    async def wrapper(*args, **kwargs):
        update: Update = args[0]
        context: ContextTypes.DEFAULT_TYPE = args[1]

        with open(config["admins"]) as admin_file:
            admins = [int(id) for id in admin_file.read().splitlines()]

        if update.effective_user.id in admins:
            await func(*args, **kwargs)
            logging.info("User %s (ID: %d) ran protected command %s" % (
                update.effective_user.first_name, update.effective_user.id, update.message.text))
        else:
            logging.info(
                "User %s (ID: %d) tried to run protected command %s but did not have permissions!" % (update.effective_user.first_name, update.effective_user.id, update.message.text))
            await context.bot.send_message(chat_id=update.effective_chat.id, text="אין לך הרשאות לכך.")

    return wrapper


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Implements /start command"""
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="ברוכים הבאים לבוט של גורדי ויובי. כדי לראות רשימה של שאלות אפשריות, יש להזין /questions")


async def available_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows the available questions from the database"""
    df = pd.read_csv(config["rules"])
    for question in df.Question.unique():
        await context.bot.send_message(chat_id=update.effective_chat.id, text=question)


async def answer_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Answers questions from the database using fuzzy weighted ratio string searching"""

    # Get csv data from file
    df = pd.read_csv(config["rules"])

    # Extract the question closest matching the user's message
    # TWEAK THE SEARCH ALGORITHM HERE
    questions = list(df.Question)
    matched_question = process.extractOne(
        update.message.text, questions, scorer=fuzz.WRatio, score_cutoff=70)

    # Send each message from the matched question to the user if a match was found
    if matched_question:
        # Log the matched question
        logging.info("User %s sent message %s, matched question %s with probability %d" %
                     (update.message.from_user.first_name, update.message.text, matched_question[0], matched_question[1]))
        results = df[df.Question == matched_question[0]]
        for result_message in results.Sentence:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=result_message)
    else:

        # Log the query and the score
        matched_question = process.extractOne(
            update.message.text, questions, scorer=fuzz.WRatio)
        logging.warn("User %s sent message %s, most closely matched question %s with probability %d" %
                     (update.message.from_user.first_name, update.message.text, matched_question[0], matched_question[1]))
        await context.bot.send_message(chat_id=update.effective_chat.id, text="סליחה, לא הצלחנו לענות על שאלתך. יש לפנות למפקידך או לרסר לקבלת מענה")
    await context.bot.send_message(chat_id=update.effective_chat.id, text="אוהבים, ג'ורדי ויובי 🇸🇭")

    with open(config["authors"], "rb") as authors:
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=authors)


def main():
    app = ApplicationBuilder().token(config["token"]).build()
    start_handler = CommandHandler('start', start)
    questions_handler = MessageHandler(
        filters.TEXT & ~(filters.COMMAND), answer_questions)
    available_questions_handler = CommandHandler(
        'questions', available_questions)
    app.add_handler(start_handler)
    app.add_handler(available_questions_handler)
    app.add_handler(questions_handler)
    app.run_polling()


if __name__ == '__main__':
    main()
