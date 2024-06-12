import socket
import struct
from collections import namedtuple

Request = namedtuple('Request', ['address', 'body'])


@staticmethod
def _receive_big(connection, buffer_size=1024) -> bytes:
    data = b''
    try:
        bs = connection.recv(8)
    except OSError:
        return
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


class ConnectionService:
    def __init__(
            self,
            bind_address: tuple = None,
            connect_address: tuple = None
    ):
        self.bind_address = bind_address
        self.connect_address = connect_address

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._connected_socket = None

    @staticmethod
    def _init_bind(sock, bind_address: tuple):
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(bind_address)
        sock.listen(1)

    @staticmethod
    def _init_connect(sock, connect_address: tuple):
        try:
            sock.settimeout(5)
            sock.connect(connect_address)
        except ConnectionRefusedError:
            return

    def init(self):
        if self.bind_address is not None:
            self._init_bind(self.socket, self.bind_address)
        if self.connect_address is not None:
            self._init_connect(self.socket, self.connect_address)
            self._connected_socket = self.socket

    def receive(self) -> Request | None:
        if self._connected_socket is None:
            self._connected_socket, _ = self.socket.accept()
        body = _receive_big(self._connected_socket)
        if not body:
            self._connected_socket.close()
            self._connected_socket = None
            return
        return Request(address=self._connected_socket.getsockname(), body=body)

    def answer(self, data: bytes):
        _send_big(self._connected_socket, data)

    def close(self):
        if self._connected_socket:
            self._connected_socket.close()
        self._connected_socket = None

