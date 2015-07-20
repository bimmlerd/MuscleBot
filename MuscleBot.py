#!/usr/bin/env python
# encoding: utf-8

'''Muscle Telegram Bot'''

__author__ = 'bimmlerd@student.ethz.ch'

import telegram
import requests
import json
import time
import re


class MuscleBotHandler:
    """ The MuscleBot Telegram bot allows you to join events on muscle.bimmler.ch in a convenient fashion via telegram.
    """
    # BASE_URL = "https://muscle.bimmler.ch/"
    BASE_URL = "http://localhost:3000/"
    API_BASE_URL = BASE_URL + "api/"

    def __init__(self, balancer, chat_id):
        self.balancer = balancer
        self.chat_id = chat_id
        self.options = None

    def send_message(self, message):
        self.balancer.send_message(message, self.chat_id)

    def handle_update(self, update):
        text = update.message.text
        chat_id = update.message.chat.id

        if not text:
            self.send_message("So sorry, I only understand text at the moment...")

        pattern = "(\d)" # only single digit choices
        match = re.search(pattern, text)
        if text == "/join":
            self._handle_join(chat_id)
        elif text == "/list":
            self.send_message("list is not yet implemented")
        elif text == "/register":
            self._handle_register()
        elif self.options and match:
            self._handle_event_choice(match.group(1))
        else:
            self.send_message("That's not something I understand" + telegram.Emoji.PILE_OF_POO)

    def _handle_join(self, chat_id):
        try:
            events = self._get_events()
            if 1 < len(events) < 10:
                message = "Which event would you like to join?\n"
                for i, event in enumerate(events, 1):
                    message += "/{0} for {1}\n".format(i, self.format_event(event))
                self.send_message(message)
                self.options = events

            elif len(events) == 1:
                event = events[0]
                self._join_event(event)
                self.send_message("Yup, you got it.")

            else:
                # e.g. more than 9 events
                raise EnvironmentError

        except EnvironmentError:
            self.send_message("Uh oh, something went wrong inside the techy heart of me 0.0")

    def _handle_event_choice(self, choice):
        index = int(choice) - 1
        if 0 <= index < len(self.options):
            event = self.options[index]
            self.send_message("You chose option {0}, which was {1}".format(choice, self.format_event(event)))
            self._join_event(event)
            self.options = None
        else:
            self.send_message("IndexOutOfBoundExcep... Nope, we're good. Not a valid choice though, so try again.")

    def _handle_register(self):
        url = self.API_BASE_URL + "integration/telegram"
        payload = {'telegram_id': self.chat_id, 'key': self.balancer.API_KEY}   # fine since over HTTPS
        data = self._request(url, payload)
        link = self.BASE_URL + "integration/login/" + data['token']
        msg = "Okay, I'm gonna send you a special link now, please open it and log into muscle if prompted:\n{}".format(link)
        self.send_message(msg)

    def _get_events(self):
        url = self.API_BASE_URL + "events/"
        return self._request(url)

    def _join_event(self, event):
        url = self.API_BASE_URL + "join/" + event['_id']
        payload = {'telegram_id': self.chat_id, 'key': self.balancer.API_KEY}   # fine since over HTTPS
        r = requests.post(url, data=payload)
        if r.status_code == 200:
            self.send_message("So that should've worked.")
        elif r.status_code == 208:
            self.send_message("You're already part of that event. I appreciate the eagerness though"
                              + telegram.Emoji.FACE_WITH_STUCK_OUT_TONGUE_AND_WINKING_EYE)
        else:
            self.send_message("Uh oh, something went kinda wrong...")
        pass

    @staticmethod
    def format_event(event):
        return "{0} at {1}".format(event['name'], time.strftime("%H:%M, %d.%m", time.localtime(event['date']/1000)))

    @staticmethod
    def _request(url, payload={}):
        response = json.loads(requests.get(url, params=payload).text)
        if response['status'] == 'success':
            data = response['data']
        else:
            raise EnvironmentError
        return data


class MuscleBotBalancer:
    """ The MuscleBotBalancer is basically a load balancer, spawns a MuscleBotHandler per conversation.
    """

    def __init__(self):
        with open("AuthToken") as f:
            token = f.readline().strip()

        with open("BotKey") as f:
            self.API_KEY = f.readline().strip()

        self.bot = telegram.Bot(token)
        self.LAST_UPDATE_ID = self.bot.getUpdates()[-1].update_id
        self.handlers = dict()  # handlers are instances of MuscleBotHandler, one for each conversation

    def run(self):
        while True:
            for update in self.bot.getUpdates(offset=self.LAST_UPDATE_ID):
                update_id = update.update_id

                if self.LAST_UPDATE_ID < update_id:  # If newer than latest update
                    self.pass_update_to_handler(update)

    def pass_update_to_handler(self, update):
        chat_id = update.message.chat.id

        if not self.handlers.has_key(chat_id):
            # spawn new handler
            self.handlers[chat_id] = MuscleBotHandler(self, chat_id)

        self.handlers[chat_id].handle_update(update)
        self.LAST_UPDATE_ID = update.update_id

    def send_message(self, message, chat_id):
        self.bot.sendMessage(chat_id=chat_id, text=message)


def main():
    balancer = MuscleBotBalancer()
    balancer.run()

if __name__ == '__main__':
    main()
