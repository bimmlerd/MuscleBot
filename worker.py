# coding: utf-8
from os import path
import sys
import config
from redis import Redis
from rq import Worker, Queue, Connection

sys.path.insert(0, path.abspath(path.dirname(__file__)))


def main():
    if not config.redis:
        sys.exit('Missing redis config')
    listen = ('high', 'default', 'reply', 'low')
    conn = Redis(**config.redis)
    with Connection(conn):
        worker = Worker(map(Queue, listen))
        worker.work()

if __name__ == '__main__':
    main()