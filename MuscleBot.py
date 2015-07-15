
#!/usr/bin/env python
# encoding: utf-8

'''Muscle Telegram Bot'''

__author__ = 'bimmlerd@student.ethz.ch'

import telegram
import requests
import json

#BASE_URL = "http://muscle.bimmler.ch/api/"
BASE_URL = "http://localhost:3000/api/"

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
                    if text == "/list":
                        response = "You wanted the latest events:"
                    elif text == "/join":
                        response = "These events are available:\n"
                        events = getEvents()
                        for i, event in enumerate(events):
                            response += "%d.\t%s\n" % (i, event['name'])

                    else:
                        response = "That's not something I understand" + telegram.Emoji.PILE_OF_POO
                    bot.sendMessage(chat_id=chat_id, text=response)
                    LAST_UPDATE_ID = update_id

def getEvents():
    url = BASE_URL + "events"
    r = requests.get(url)
    data = json.loads(r.text)['data']
    return data

if __name__ == '__main__':
    main()