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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Implements /start command"""
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="ברוכים הבאים לבוט של גורדי ויובי")


async def available_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows the available questions from the database"""
    df = pd.read_csv(config["rules"])
    for question in df.Question.unique():
        await context.bot.send_message(chat_id=update.effective_chat.id, text=question)


async def answer_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Answers questions from the database using fuzzy partial ratio string searching"""

    # Get csv data from file
    df = pd.read_csv(config["rules"])

    # Extract the QuestionID of the question closest matching the user's message
    # TWEAK THE SEARCH ALGORITHM HERE
    questions = list(df.Question)
    matched_question = process.extractOne(
        update.message.text, questions, scorer=fuzz.token_sort_ratio, score_cutoff=70)

    # Send each message from the matched question to the user if a match was found
    if matched_question:
        # Log the matched question
        logging.info(f"User {update.message.from_user.first_name} sent message {update.message.text}, \
         closest match to question {matched_question[0]} with probability {matched_question[1]}")
        results = df[df.Question == matched_question[0]]
        for result_message in results.Sentence:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=result_message)
    else:
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
