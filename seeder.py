import socket
from dataclasses import dataclass
import struct
import ipaddress
import threading


@dataclass
class AddToBookPacket:
    ip: str
    port: int

    @classmethod
    def from_bytes(cls, data: bytes):
        if not data:
            return
        try:
            if len(data) == 7:
                data = data[1:]  # Cut request type
            ip_int, port = struct.unpack('>IH', data)
        except struct.error as e:
            print(e, data, len(data))
        return cls(
            ip=str(ipaddress.ip_address(ip_int)),
            port=port
        )

    def to_bytes(self) -> bytes:
        return struct.pack('>IH', int(ipaddress.IPv4Address(self.ip)), self.port)

    def to_tuple(self) -> tuple[str, int]:
        return (self.ip, self.port)

    def __str__(self):
        return f'{self.ip}:{self.port}'


address_book: list[AddToBookPacket] = []

server_socket = socket.socket()
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(('0.0.0.0', 9998))
server_socket.listen(3)
print("Listening for clients on", ('0.0.0.0', 9998))


def send_big(connection, data: str | bytes):
    if not isinstance(data, bytes):
        data = data.encode()
    data_length = struct.pack('>Q', len(data))
    connection.sendall(data_length)
    connection.sendall(data)


def check_address_book_clients_alive():
    for address in address_book.copy():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        result = s.connect_ex(address.to_tuple())
        if result != 0 and address in address_book:
            print(f"Remove", address, 'due to not alive with status =', result)
            address_book.remove(address)
        s.close()


def handle_client(client_socket):
    raw_packet = client_socket.recv(512)
    raw_packet = raw_packet[8:]  # Cut packet size

    packet = AddToBookPacket.from_bytes(raw_packet)
    if packet is None:
        client_socket.send(b'Invalid addtobook packet')
        client_socket.close()
        return
    
    if packet not in address_book:
        print(packet, "added to book")
        address_book.append(packet)

    check_address_book_clients_alive()
    address_book_dumped = b''.join(map(lambda i: i.to_bytes(), address_book))
    print("sending", address_book_dumped)
    send_big(client_socket, address_book_dumped)
    client_socket.close()


def receive_clients():
    while True:
        client_socket, client_address = server_socket.accept()
        threading.Thread(target=handle_client, args=(client_socket,)).start()


try:
    receive_clients()
except KeyboardInterrupt:
    print("Stopping seeder...")
    server_socket.close()

