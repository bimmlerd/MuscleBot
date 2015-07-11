#!/usr/bin/env python
# encoding: utf-8

'''Muscle Telegram Bot'''

__author__ = 'bimmlerd@student.ethz.ch'

import telegram
import requests


def main():
    f = open("AuthToken")
    token = f.read().strip()

    bot = telegram.Bot(token)  # Telegram Bot Authorization Token

    global LAST_UPDATE_ID
    LAST_UPDATE_ID = bot.getUpdates()[-1].update_id  # Get latest update

    while True:
        for update in bot.getUpdates(offset=LAST_UPDATE_ID):
            text = update.message.text
            chat_id = update.message.chat.id
            update_id = update.update_id

            if LAST_UPDATE_ID < update_id:  # If newer than latest update
                if text:
                    response = "You said \"%s\"" % text 
                    bot.sendMessage(chat_id=chat_id, text=response)
                    LAST_UPDATE_ID = update_id

if __name__ == '__main__':
    main()
