import asyncio
import websockets
import logging
from random import random
import functools
import json

logger = logging.getLogger()

class WebsocketServer:
    def __init__(self, url='localhost', port=8848, consumer_handler=None, producer_handler=None):
        self._url = url
        self._port = port
        self._consumer_handler = WebsocketServer._default_consumer_handler
        self._producer_handler = WebsocketServer._default_producer_handler

    def make_consumer(self, consumer=None):
        if consumer is None:
            self._consumer = {
                'func': WebsocketServer._default_consumer,
                'desc': "This consumer append 'Hello' before the received message"
            }
        else:
            self._consumer = consumer
        partial_consumer_handler = functools.partial(self._consumer_handler, consumer=self._consumer['func'])
        self._server = websockets.serve(partial_consumer_handler, 'localhost', 8848)
        self._description = self._consumer['desc']
        return self

    def make_producer(self, producer=None):
        if producer is None:
            self._producer = {
                'func': WebsocketServer._default_producer,
                'desc': "This producer generates a random number per second"
            }
        else:
            self._producer = producer
        partial_producer_handler = functools.partial(self._producer_handler, producer=self._producer['func'])
        self._server = websockets.serve(partial_producer_handler, 'localhost', 8848)
        self._description = self._producer['desc']
        return self

    @staticmethod
    async def _default_consumer_handler(websocket, path, consumer):
        while True:
            logger.info('Responding to connection...')
            message = await websocket.recv()
            result = await consumer(message)
            await websocket.send(result)

    @staticmethod
    def _default_consumer(message):
        logger.info(f"< {message}")
        greeting = f"Hello {message}!"
        logger.info(f"> {greeting}")
        return greeting

    @staticmethod
    async def _default_producer_handler(websocket, path, producer):
        while True:
            message = await producer()
            message = json.dumps(message)
            logger.debug(message)
            await websocket.send(message)

    @staticmethod
    async def _default_producer():
        await asyncio.sleep(1)
        return random()

    def start(self):
        logger.info("Starting websocket server at: %s", "http://localhost:8848")
        logger.info(self._description)
        asyncio.get_event_loop().run_until_complete(self._server)
        asyncio.get_event_loop().run_forever()

    def stop(self):
        logger.info('Stopping websocket server')
        asyncio.get_event_loop().stop()

if __name__ == '__main__':
    import sys
    import time
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    server = WebsocketServer()
    server.make_producer().start()