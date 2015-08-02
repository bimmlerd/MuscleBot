# coding: utf-8
import json
import flask
from flask import request
import telegram
import config
import MuscleBot

__bot_name__ = 'MuscleBot'

app = flask.Flask(__name__)
balancer = MuscleBot.MuscleBotBalancer()


@app.route("/%s" % config.WEBHOOK_TOKEN, methods=['POST'])
def webhook():
    """ Receive telegram updates in this webhook """
    _update = request.json
    if app.debug:
        print json.dumps(_update, indent=2)
    try:
        updates = [telegram.Update.de_json(x) for x in _update.get('result')]
        for update in updates:
            balancer.pass_update_to_handler(update)
    except:
        raise EnvironmentError
    return ''


def main():
    app.run(host='0.0.0.0', port=config.PORT,
            ssl_context=("muscle.bimmler.ch.crt", "muscle.bimmler.ch.key"))

if __name__ in ['__main__', __bot_name__]:
    main()
