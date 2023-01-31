#!/bin/env python3

# Imports
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (filters, ApplicationBuilder, ContextTypes,
                          CommandHandler, MessageHandler, ConversationHandler,
                          CallbackQueryHandler)
from config import config
import pandas as pd
from thefuzz import process, fuzz

# Initialize logging module
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Conversation states for add_question conversation handler
QUESTION, REPLIES, CONFIRM = range(3)


def admin_required(func) -> function:
    """Decorator function for requiring admin access"""
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

# Functions for new_question conversation handler


@admin_required
async def new_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Allows an admin user to add a new question to the bot"""
    await update.message.reply_text("היי מנהל יקר, איזה שאלה תרצה להוסיף? תזין /cancel בכל עת בתהליך כדי לבטל את הפעולה.")
    return QUESTION


async def add_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Gets the new question from the user and saves it to the user_data"""
    question = update.message.text
    context.user_data["question"] = question
    await update.message.reply_text("תתחיל לכתוב את התשובה. התשובה יכולה להיות מספר הודעות. על מנת לסמן לי שסיימת לכתוב תשובות, יש לשלוח /done.")
    return REPLIES


async def add_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Gets new replies for the question from the user and saves them to user_data"""
    reply = update.message.text
    
    # Initializes the list of replies
    if not context.user_data["replies"]:
        context.user_data["replies"] = []
    
    # Adds the reply
    context.user_data["replies"].append(reply)

    # Continues the loop in conversation state
    return REPLIES


async def finish_add_question(update: Update, context: ContextTypes) -> int:
    user_data = context.user_data
    question = user_data["question"]
    replies = user_data["replies"]
    logging.info("User %s added new question %s" % (update.effective_user.first_name, question))
    df = pd.read_csv(config["rules"])
    
    return ConversationHandler.END
# Normal command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Implements /start command"""
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="ברוכים הבאים לבוט של גורדי ויובי. כדי לראות רשימה של שאלות אפשריות, יש להזין /questions")


async def available_questions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows the available questions from the database"""
    df = pd.read_csv(config["rules"])
    for question in df.Question.unique():
        await context.bot.send_message(chat_id=update.effective_chat.id, text=question)

# Message handlers


async def answer_questions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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


def main() -> None:
    app = ApplicationBuilder().token(config["token"]).build()
    start_handler = CommandHandler('start', start)
    new_question_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("new-question", new_question)],
        states={
            QUESTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_question)
            ],
            REPLIES: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_reply),
                CommandHandler("done", finish_add_question)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel_add_question)]
    )
    questions_handler = MessageHandler(
        filters.TEXT & ~(filters.COMMAND), answer_questions)
    available_questions_handler = CommandHandler(
        'questions', available_questions)
    app.add_handler(start_handler)
    app.add_handler(new_question_conv_handler)
    app.add_handler(available_questions_handler)
    app.add_handler(questions_handler)
    app.run_polling()


if __name__ == '__main__':
    main()
