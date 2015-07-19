#!/usr/bin/env python
# encoding: utf-8

'''Muscle Telegram Bot'''

__author__ = 'bimmlerd@student.ethz.ch'

import telegram
import requests
import json
import time
import shelve


class MuscleBot:
    """ The MuscleBot Telegram bot allows you to join events on muscle.bimmler.ch in a convenient fashion via telegram.
    """

    API_BASE_URL = "http://localhost:3000/api/"

    def __init__(self):
        f = open("AuthToken")
        token = f.read().strip()
        f.close()
        self.bot = telegram.Bot(token)

        self.LAST_UPDATE_ID = self.bot.getUpdates()[-1].update_id

    def run(self):
        while True:
            for update in self.bot.getUpdates(offset=self.LAST_UPDATE_ID):
                update_id = update.update_id

                if self.LAST_UPDATE_ID < update_id:  # If newer than latest update
                    self.handle_update(update)

    def handle_update(self, update):
        update_id = update.update_id
        text = update.message.text
        chat_id = update.message.chat.id

        if not text:
            self.bot.sendMessage(chat_id=chat_id, text="So sorry, I only understand text at the moment...")
            self.LAST_UPDATE_ID = update_id
            return

        if text == "/join":
            response = self._handle_join(chat_id)
        elif text == "/list":
            response = "nope not yet"
        else:
            response = "That's not something I understand" + telegram.Emoji.PILE_OF_POO
        self.bot.sendMessage(chat_id=chat_id, text=response)
        self.LAST_UPDATE_ID = update_id

    def _handle_join(self, chat_id):
        try:
            events = self._get_events()
            if len(events) > 1:
                response = "Which event would you like to join?\n"
                for i, event in enumerate(events, 1):
                    response += "/{0} for {1}\n".format(i, self.format_event(event))
                # TODO!!
            else:
                event = events[0]
                self._join_event(event)
                response = "Yup, you got it."

        except EnvironmentError:
            response = "Uh oh, something went wrong inside the techy heart of me 0.0"
        return response

    def _get_events(self):
        url = self.API_BASE_URL + "events/"
        return self._request(url)

    def _join_event(self):
        print "Totally would have tried to join an event now."
        pass

    @staticmethod
    def format_event(self, event):
        return "{0} at {1}".format(event['name'], time.strftime("%H:%M on %d.%m", time.localtime(event['date']/1000)))

    @staticmethod
    def _request(self, url):
        response = json.loads(requests.get(url).text)
        if response['status'] == 'success':
            data = response['data']
        else:
            raise EnvironmentError
        return data


def main():
    bot = MuscleBot()

    keys = shelve.open("IDKeyMap")
    try:
        bot.run()
    finally:
        keys.close()


if __name__ == '__main__':
    main()
