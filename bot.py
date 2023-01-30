#!/bin/env python3

# Imports
from datetime import datetime
import csv
import os
from thefuzz import fuzz, process
import requests
from config import config

TOKEN = config["token"]
PROXIES = {
    'http': 'http://10.0.0.10:80',
    'https': 'http://10.0.0.10:80',
}
QUESTION_ID = 0
QUESTION = 1
SENTENCE_ID = 2
SENTENCE = 3
LABEL = 4
RULES_FILE = R"C:\Users\u2225622\Desktop\WikiQACorpus\AlphaRules.csv"


class BotHandler:

    def __init__(self, token):
        self.token = token
        self.api_url = "https://api.telegram.org/bot{}/".format(token)

    def get_updates(self, offset=None, timeout=30):
        method = 'getUpdates'
        params = {'timeout': timeout, 'offset': offset}
        resp = requests.get(self.api_url + method, params, proxies=PROXIES)
        result_json = resp.json()['result']
        return result_json

    def send_message(self, chat_id, text):
        params = {'chat_id': chat_id, 'text': text}
        method = 'sendMessage'
        resp = requests.post(self.api_url + method, params, proxies=PROXIES)
        return resp

    def send_photo(self, chat_id, photo):
        params = {'chat_id': chat_id, 'photo': photo}
        method = 'sendPhoto'
        resp = requests.post(self.api_url + method, params, proxies=PROXIES)
        return resp

    def get_last_update(self):
        get_result = self.get_updates()

        if len(get_result) > 0:
            last_update = get_result[-1]
        else:
            last_update = get_result
        return last_update

    def write_chats(self, filename, information):
        path = os.path.join(config["logs_dir"], filename)
        new = open(path, "a", encoding="utf-8")
        new.write(str(datetime.now().ctime())+"\n")
        new.write(str(information) + "\n")


greet_bot = BotHandler(TOKEN)


rate = 77


def main():
    new_offset = None

    while True:
        greet_bot.get_updates(new_offset)

        last_update = greet_bot.get_last_update()
        print("LAST UPDATE: ", type(last_update), "\n", last_update)

        commands = {
            "/start": "ברוכים הבאים לבוט של גורדי ויובי"
        }

        if type(last_update) != list:
            last_update_id = last_update['update_id']
            last_chat_text = last_update['message']['text']
            print(last_chat_text, len(last_chat_text), type(last_chat_text))
            last_chat_id = last_update['message']['chat']['id']
            last_chat_name = last_update['message']['chat']['first_name']
            try:
                first_chat_name = last_update['message']['chat']['last_name']
            except:
                first_chat_name = "none"

            n = 0

            # Handle commands
            if last_chat_text in commands:
                greet_bot.send_message(last_chat_id, commands[last_chat_text])

            else:

                with open(RULES_FILE, newline='', encoding="utf-8") as rules_file:
                    reader = csv.reader(rules_file)
                    data = list(reader)
                    questions = [row[QUESTION] for row in data]
                    result = process.extractOne(
                        last_chat_text, questions, scorer=fuzz.token_set_ratio)
                    if result:
                        print("L ", result[1])
                        print("P ", result[0])

                        # Get all results for question
                        answers = [phrase[SENTENCE]
                                   for phrase in data if phrase[QUESTION] == result[0]]
                        for answer in answers:
                            greet_bot.send_message(last_chat_id, answer)
                        n += 1
                    # for phrase in data:
                    #     leven = fuzz.partial_ratio(
                    #         last_chat_text.lower(), phrase[QUESTION])

                    #     if leven >= rate:
                    #         print("Understand")
                    #         possible_match = phrase[QUESTION]
                    #         print("L ", leven)
                    #         print("P ", possible_match)

                    #         if phrase[QUESTION] == possible_match:
                    #             greet_bot.send_message(last_chat_id, phrase[SENTENCE])
                    #             n += 1
                    #         else:
                    #             pass

                    if n == 0:
                        greet_bot.send_message(
                            last_chat_id, 'לא הצלחתי למצוא תשובה, {}, ממליצים לפנות לרסר לתשובה.'.format(last_chat_name))
                    else:
                        greet_bot.send_message(
                            last_chat_id, 'מקווה שעזרנו, {}, יוביבי וגורדי.❤️🇸🇭❤️🇸🇭'.format(last_chat_name))
                        greet_bot.send_photo(
                            last_chat_id, "https://imgur.com/a/PUOLOn9")

            greet_bot.write_chats(last_chat_name+"_" +
                                  first_chat_name, last_update)
            new_offset = last_update_id + 1

        else:
            print("No updates")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit()
