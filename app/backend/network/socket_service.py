import socket
import threading
import os
import struct
from app.backend.network.models import Request


class SocketService:
    def __init__(self, bind_address: tuple,
                 response_factory, request_factory):
        self.socket = socket.socket()
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(bind_address)
        self.socket.listen(1)

        self.response_factory = response_factory
        self.request_factory = request_factory

        self.address_book = []
        self.bind_address = bind_address

    def init(self):
        t = threading.Thread(target=self.accept_connections)
        t.start()

    @staticmethod
    def _receive_big(connection, buffer_size=1024) -> bytes:
        data = b''
        bs = connection.recv(8)
        if not bs:
            return b''
        (data_length,) = struct.unpack('>Q', bs)
        while len(data) < data_length:
            to_read = data_length - len(data)
            try:
                data += connection.recv(buffer_size if to_read > buffer_size else to_read)
            except ConnectionResetError:
                return b''
        return data

    @staticmethod
    def _send_big(connection, data: str | bytes):
        if not isinstance(data, bytes):
            data = data.encode()
        data_length = struct.pack('>Q', len(data))
        try:
            connection.sendall(data_length)
            connection.sendall(data)
        except (BrokenPipeError, OSError):
            pass

    def _handle_request(self, request_socket):
        request_raw = self._receive_big(request_socket)
        request = self.request_factory.undump(request_raw)
        if request is None:
            return
        
        self.request_factory.handle_request(request)
        response = self.response_factory.make_response_from_request(request)
        if response is not None:
            self._send_big(request_socket, response)

    def accept_connections(self):
        while True:
            client_socket, _ = self.socket.accept()
            self._handle_request(client_socket)
            client_socket.close()

    def _do_public_request(self, request) -> list[bytes]:
        responses = []
        for address in self.address_book:
            if address == self.bind_address:
                continue
            s = socket.socket()
            s.connect(address)
            self._send_big(s, request.packed)
            if request.have_response:
                responses.append(self._receive_big(s))
            s.close()
        return responses

    def _do_direct_request(self, request, receiver) -> bytes | None:
        response = None
        s = socket.socket()
        s.connect(receiver)
        self._send_big(s, request.packed)
        if request.have_response:
            response = self._receive_big(s)
        s.close()
        return response

    def do_request(self, request: Request, receiver: tuple[str, int] | None = None) -> list[bytes]:
        if receiver:
            response = self._do_direct_request(request, receiver)
            return [response]
        return self._do_public_request(request)

