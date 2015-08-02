# coding: utf-8
import telegram
import requests
import json
import time
import re
import config
from rq.decorators import job

__author__ = 'bimmlerd@student.ethz.ch'


class MuscleBotHandler:
    """ The MuscleBot Telegram bot allows you to join events on muscle.bimmler.ch in a convenient fashion.
    """
    BASE_URL = "https://muscle.bimmler.ch/"
    API_BASE_URL = BASE_URL + "api/"

    def __init__(self, balancer, chat_id):
        self.balancer = balancer
        self.chat_id = chat_id
        self.options = None

    def send_message(self, message):
        self.balancer.send_message(message, self.chat_id)

    @job('reply', connection=config.redis, result_ttl=5)
    def handle_update(self, update):
        text = update.message.text

        if not text:
            self.send_message("So sorry, I only understand text at the moment...")
            return

        pattern = "/(\d)" # only single digit choices
        match = re.search(pattern, text)
        if text == "/join":
            self._handle_join()
        elif text == "/leave":
            self._handle_leave()
        elif text == "/list":
            self._handle_list()
        elif text == "/register":
            self._handle_register()
        elif self.options and match:
            self._handle_event_choice(match.group(1))
        elif match and not self.options:
            self.send_message("You already completed the menu flow.")
        else:
            self.send_message("That's not something I understand" + telegram.Emoji.PILE_OF_POO)

    def _handle_join(self):
        try:
            events = self._get_events()
            if 1 < len(events) < 10:
                message = "Which event would you like to join?\n"
                for i, event in enumerate(events, 1):
                    message += "/{0} for {1}\n".format(i, self.format_event(event))
                self.send_message(message)
                self.options = events
                self.action = self._join_event
            elif len(events) == 1:
                event = events[0]
                self._join_event(event)
            elif not events:
                self.send_message("No events are joinable at this point.")
            else:
                # e.g. more than 9 events
                raise EnvironmentError

        except EnvironmentError:
            self.send_message("Uh oh, something went wrong inside the techy heart of me 0.0")

    def _handle_leave(self):
        try:
            events = self._get_events()
            if 1 < len(events) < 10:
                message = "Which event would you like to leave?\n"
                for i, event in enumerate(events, 1):
                    message += "/{0} for {1}\n".format(i, self.format_event(event))
                self.send_message(message)
                self.options = events
                self.action = self._leave_event
            elif len(events) == 1:
                event = events[0]
                self._leave_event(event)
            elif not events:
                self.send_message("No events available.")
            else:
                # e.g. more than 9 events
                raise EnvironmentError

        except EnvironmentError:
            self.send_message("Uh oh, something went wrong inside the techy heart of me 0.0")

    def _handle_event_choice(self, choice):
        index = int(choice) - 1
        if 0 <= index < len(self.options):
            event = self.options[index]
            self.action(event)
        else:
            self.send_message("IndexOutOfBoundExcep... Nope, we're good. Not a valid choice though, so try again.")

    def _handle_register(self):
        url = self.API_BASE_URL + "integration/telegram"
        payload = {'telegram_id': self.chat_id, 'key': self.balancer.API_KEY}   # fine since over HTTPS
        data = self._request(url, payload)
        link = self.BASE_URL + "integration/login/" + data['token']
        msg = "Okay, I'm gonna send you a special link now, please open it and log into muscle if prompted:\n{}".format(link)
        self.send_message(msg)

    def _handle_list(self):
        events = self._get_events()
        msg = "The following events can be joined:\n"
        for event in events:
            msg += self.format_event(event) + "\n"
        self.send_message(msg)

    def _get_events(self):
        url = self.API_BASE_URL + "events/"
        return self._request(url)

    def _join_event(self, event):
        url = self.API_BASE_URL + "join/" + event['_id']
        payload = {'telegram_id': self.chat_id, 'key': self.balancer.API_KEY}   # fine since over HTTPS
        r = requests.post(url, data=payload)
        if r.status_code == 200:
            self.send_message("Okidoke, you'll get your weights.")
            self.options = None
            self.action = None
        elif r.status_code == 208:
            self.send_message("You're already part of that event. I appreciate the eagerness though"
                              + telegram.Emoji.FACE_WITH_STUCK_OUT_TONGUE_AND_WINKING_EYE)
        elif r.status_code == 412:
            self.send_message("You need to register you telegram account with muscle before you can join events. "
                              "Try /register.")
        else:
            self.send_message("Uh oh, something went kinda wrong...")

    def _leave_event(self, event):
        url = self.API_BASE_URL + "leave/" + event['_id']
        payload = {'telegram_id': self.chat_id, 'key': self.balancer.API_KEY}   # fine since over HTTPS
        r = requests.post(url, data=payload)
        if r.status_code == 200:
            self.send_message("Okidoke, you're out.")
            self.options = None
            self.action = None
        elif r.status_code == 208:
            self.send_message("You're not even part of that event. Wat.")
        elif r.status_code == 412:
            self.send_message("You need to register you telegram account with muscle before you can leave events. "
                              "Try /register.")
        else:
            self.send_message("Uh oh, something went kinda wrong...")

    @staticmethod
    def format_event(event):
        return "{0} at {1}".format(event['name'], time.strftime("%H:%M, %d.%m.%y", time.localtime(event['date']/1000)))

    @staticmethod
    def _request(url, payload=None):
        if not payload:
            payload = {}
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
        token = config.TOKEN
        self.API_KEY = config.API_KEY
        self.WEBHOOK_TOKEN = config.WEBHOOK_TOKEN
        self.WEBHOOK_HOSTNAME = config.PATH

        self.bot = telegram.Bot(token)
        self.handlers = dict()  # handlers are instances of MuscleBotHandler, one for each conversation
        self.bot.setWebhook(self.WEBHOOK_HOSTNAME)

    def pass_update_to_handler(self, update):
        chat_id = update.message.chat.id

        if not self.handlers.has_key(chat_id):
            self.handlers[chat_id] = MuscleBotHandler(self, chat_id) # spawn new handler

        self.handlers[chat_id].handle_update.delay(update)

    def send_message(self, message, chat_id):
        self.bot.sendMessage(chat_id=chat_id, text=message)

