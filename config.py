# coding: utf-8
from os import path
import json

from redis_wrap import SYSTEMS

__name__ = 'MuscleBot'
__bot__ = 'MuscleBot'
__config__ = path.abspath(path.join(path.dirname(__file__), 'config.json'))

with open(__config__, 'r') as cf:
    config = json.loads(cf.read())

TOKEN = config.get('token')
SERVER = config.get('server')
PORT = config.get('port')
WEBHOOK_TOKEN = config.get('webhook_token')
API_KEY = config.get('API_key')

PATH = '%s:%s/%s' % (SERVER.strip('/'), PORT, WEBHOOK_TOKEN)

redis = SYSTEMS['default'] ## fix this if your config.json isn't default