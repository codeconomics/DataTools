import asyncio
import websockets
import logging
import functools
import numpy as np

logger = logging.getLogger()

class WebsocketClient:
    def __init__(self, url='localhost', port=8848, consumer_handler=None, producer_handler=None):
        self._url = url
        self._port = port
        if consumer_handler is None:
            self._consumer_handler = WebsocketClient._default_consumer_handler
        else:
            self._consumer_handler = consumer_handler
        # if producer_handler is None:
        #     self._producer_handler = WebsocketClient._default_producer_handler
        # else:
        #     self._producer_handler = producer_handler

    def make_consumer(self, consumer=None):
        if consumer is None:
            self._consumer = WebsocketClient._default_consumer
        else:
            self._consumer = consumer
        self._handler = functools.partial(self._consumer_handler, url=self._url, port=self._port, consumer=self._consumer)
        return self

    @staticmethod
    async def _default_consumer_handler(url, port, consumer):
        server_addr = 'ws://' + str(url) + ':' + str(port)
        async with websockets.connect(server_addr) as websocket:
            logger.info('Connected to websocket server: ' + server_addr)
            while True:
                message = await websocket.recv()
                #logger.info('< ' + message)
                result = await consumer(message)
                #logger.info('> ' + str(result))
                await websocket.send(result)

    @staticmethod
    async def _default_consumer(message):
        return 'Got it!'

    def start(self):
        asyncio.get_event_loop().run_until_complete(self._handler())

if __name__ == '__main__':
    import sys
    import time
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    client = WebsocketClient()
    client.make_consumer().start()