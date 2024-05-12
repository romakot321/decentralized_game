import socket
import os
import threading
import time
from struct import pack, unpack
from enum import Enum
import datetime as dt
from backend.database.models import Block


class RequestType(Enum):
    get_blocks = b'\00'
    new_block = b'\01'
    new_transaction = b'\02'


class Server:
    def __init__(self, bind_address: tuple):
        self.socket = socket.socket()
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(bind_address)
        self.socket.listen(3)

        t = threading.Thread(target=self.accept_connections)
        t.start()

    @staticmethod
    def _receive_big(connection, buffer_size=1024) -> bytes:
        data = b''
        bs = connection.recv(8)
        (data_length,) = unpack('>Q', bs)
        print(f"Receiving {data_length} bytes")
        while len(data) < data_length:
            to_read = data_length - len(data)
            data += connection.recv(buffer_size if to_read > buffer_size else to_read)
        return data

    @staticmethod
    def _send_big(connection, data: str | bytes, buffer_size=1024):
        if not isinstance(data, bytes):
            data = data.encode()
        data_length = pack('>Q', len(data))
        try:
            connection.sendall(data_length)
            connection.sendall(data)
        except (BrokenPipeError, OSError):
            pass

    def _handle_request(self, request_socket):
        data = request_socket.recv(1)
        if not data:
            return
        answer = RequestHandler(request_socket, data, self.block_rep).handle()
        if answer is not None:
            self._send_big(request_socket, answer)

    def accept_connections(self):
        while True:
            client_socket, _ = self.socket.accept()
            self._handle_request(client_socket)
            client_socket.close()


class NetworkHandler(Server):
    SEEDER_ADDRESS = os.getenv('SEEDER_ADDRESS', 'localhost:9998').split(':')
    SEEDER_ADDRESS = (SEEDER_ADDRESS[0], int(SEEDER_ADDRESS[1]))

    def __init__(self, bind_address: tuple, block_repository):
        super().__init__(bind_address)
        self.address_book = []
        self.address = bind_address
        self.block_rep = block_repository

        self._last_book_update = dt.datetime.now()

    @staticmethod
    def _encode_address(address: tuple) -> bytes:
        return ':'.join(map(str, address)).encode()

    @staticmethod
    def _decode_addresses(addresses: str) -> list[tuple]:
        assert ':' in addresses, f'Maybe invalid data received: {addresses}'
        return [(addr.split(':')[0], int(addr.split(':')[1])) for addr in addresses.split(';')]

    def update_address_book(self):
        seeder_connection = socket.socket()
        seeder_connection.connect(self.SEEDER_ADDRESS)
        seeder_connection.send(self._encode_address(self.address))
        dumped_address_book = self._receive_big(seeder_connection).decode()
        self.address_book = self._decode_addresses(dumped_address_book)
        if self.address in self.address_book:
            self.address_book.remove(self.address)
        print("Address book:", self.address_book)

    def _do_request(
            self,
            request_type: RequestType,
            request_body: str | None = None,
            read_response: bool = True
    ) -> list[str]:
        responses = []
        for addr in self.address_book:
            s = socket.socket()
            s.connect(addr)
            s.sendall(request_type.value)
            if request_body:
                self._send_big(s, request_body)
            if read_response:
                responses.append(self._receive_big(s).decode())
            s.shutdown(socket.SHUT_WR)
            s.close()
        return responses

    def request_get_blocks(self):
        responses = self._do_request(RequestType.get_blocks)
        for raw_chain in responses:
            chain = list(map(lambda i: Block.undump(i), raw_chain.split('~')))
            self.block_rep.replace_chain(chain)

    def request_new_block(self, block):
        block_raw = block.dump().encode()
        self._do_request(RequestType.new_block, block_raw, read_response=False)

    def _handle_request(self, *args, **kwargs):
        super()._handle_request(*args, **kwargs)
        if (dt.datetime.now() - self._last_book_update).seconds >= 10:
            self.update_address_book()  # Check alive each request
            self._last_book_update = dt.datetime.now()


class RequestHandler:
    def __init__(self, request_socket: socket.socket, request_data: bytes, block_rep):
        self.socket = request_socket
        self.data = request_data
        self.block_rep = block_rep

    def handle(self) -> bytes:
        """Return answer for request"""
        request_type = RequestType(self.data)
        if request_type == RequestType.get_blocks:
            return self._prepare_get_blocks_answer()
        if request_type == RequestType.new_block:
            return self._handle_new_block()

    def _prepare_get_blocks_answer(self) -> bytes:
        data = '~'.join([block.dump() for block in self.block_rep.get_many()])
        return data.encode()

    def _handle_new_block(self):
        block_raw = NetworkHandler._receive_big(self.socket).decode()
        block = Block.undump(block_raw)
        self.block_rep.store(block)

