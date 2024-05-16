import os
import datetime as dt
from app.backend.database.models import Block
from app.backend.utils import asdict

import threading


class NetworkRepository:
    SEEDER_ADDRESS = os.getenv('SEEDER_ADDRESS', '127.0.0.1:9998').split(':')
    SEEDER_ADDRESS = (SEEDER_ADDRESS[0], int(SEEDER_ADDRESS[1]))

    def __init__(self, socket_service, database_repository,
                 request_factory, response_factory):
        self.socket_service = socket_service
        self.request_factory = request_factory
        self.response_factory = response_factory
        self.db_rep = database_repository

        self._last_address_book_update = dt.datetime.now() - dt.timedelta(seconds=10)

    def init(self):
        self.socket_service.init()
        threading.Thread(target=self._node_life_cycle).start()

    def _update_address_book(self):
        if (dt.datetime.now() - self._last_address_book_update).seconds >= 10:
            self.request_get_address_book()
            self._last_address_book_update = dt.datetime.now()

    def _node_life_cycle(self):
        while True:
            self._update_address_book()

    def request_get_blocks(self) -> list[Block]:
        request = self.request_factory.make_get_blocks()
        raw_responses = self.socket_service.do_request(request)
        raw_response = max(raw_responses, default=[])
        if not raw_response:
            return []
        response = self.response_factory.make_get_blocks(raw_response)
        return [
            self.db_rep.make_block(**asdict(net_block))
            for net_block in response.body
        ]

    def request_get_address_book(self):
        request = self.request_factory.make_get_address_book(body=self.socket_service.bind_address)
        raw_response = self.socket_service.do_request(request, receiver=self.SEEDER_ADDRESS)[0]
        response = self.response_factory.make_get_address_book(raw_response)
        self.socket_service.address_book = response.body

    def request_publish_block(self, block: Block):
        request = self.request_factory.make_publish_block(body=block)
        self.socket_service.do_request(request)

