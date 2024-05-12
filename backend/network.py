import socket
import os
import threading
import time
from struct import pack, unpack
from enum import Enum
import datetime as dt


class RequestType(Enum):
    get_blocks = b'\00'
    new_block = b'\01'
    new_transaction = b'\02'


class NetworkHandler:
    SEEDER_ADDRESS = os.getenv('SEEDER_ADDRESS', 'localhost:9998').split(':')
    SEEDER_ADDRESS = (SEEDER_ADDRESS[0], int(SEEDER_ADDRESS[1]))

    def __init__(self, bind_address: tuple, block_repository):
        self.socket = socket.socket()
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(bind_address)
        self.socket.listen(1)

        self.address_book = []
        self.address = bind_address
        self.block_rep = block_repository

        t = threading.Thread(target=self.accept_connections)
        t.start()

    @staticmethod
    def _encode_address(address: tuple) -> bytes:
        return ':'.join(map(str, address)).encode()

    @staticmethod
    def _decode_addresses(addresses: str) -> list[tuple]:
        assert ':' in addresses, f'Maybe invalid data received: {addresses}'
        return [(addr.split(':')[0], int(addr.split(':')[1])) for addr in addresses.split(';')]

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

    def update_address_book(self):
        seeder_connection = socket.socket()
        seeder_connection.connect(self.SEEDER_ADDRESS)
        seeder_connection.send(self._encode_address(self.address))
        dumped_address_book = self._receive_big(seeder_connection).decode()
        self.address_book = self._decode_addresses(dumped_address_book)
        print("Address book:", self.address_book)

    def update_blocks(self):
        for addr in self.address_book:
            if addr == self.address:
                continue
            s = socket.socket()
            s.connect(addr)
            s.sendall(RequestType.get_blocks.value)
            data = self._receive_big(s).decode()
            self.block_rep.update_chain(data.split('~'))
            s.shutdown(socket.SHUT_WR)
            s.close()

    def translate_new_block(self, block):
        block_raw = block.dump().encode()
        for addr in self.address_book:
            if addr == self.address:
                continue
            s = socket.socket()
            s.connect(addr)
            s.sendall(RequestType.new_block.value)
            self._send_big(s, block_raw)
            ack = s.recv(1)
            s.shutdown(socket.SHUT_WR)
            s.close()

    def accept_connections(self):
        last_book_update = dt.datetime.now() - dt.timedelta(seconds=10)
        while True:
            print((dt.datetime.now() - last_book_update).seconds)
            if (dt.datetime.now() - last_book_update).seconds >= 10:
                print("updating")
                self.update_address_book()
                last_book_update = dt.datetime.now()

            try:
                client_socket, client_address = self.socket.accept()
                print("receive", client_address)
                data = client_socket.recv(1)
                if not data:
                    continue
                answer = RequestHandler(client_socket, data, self.block_rep).handle()
                self._send_big(client_socket, answer)
            finally:
                try:
                    client_socket.shutdown(socket.SHUT_WR)
                except OSError:
                    pass
                client_socket.close()


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
        data = '~'.join([block.dump() for block in self.block_rep.iterate_blocks()])
        return data.encode()

    def _handle_new_block(self):
        block_raw = NetworkHandler._receive_big(self.socket).decode()
        self.block_rep.add_received_block(block_raw)
        return b'\00'


if __name__ == '__main__':
    BIND_ADDRESS = os.getenv('BIND_ADDRESS', '127.0.0.1:8989').split(':')
    BIND_ADDRESS = (BIND_ADDRESS[0], int(BIND_ADDRESS[1]))
    nh = NetworkHandler(BIND_ADDRESS)
    nh.update_address_book()
    print(nh.address_book)
    threading.Thread(target=nh.accept_connections).start()

