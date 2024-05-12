import socket
from dataclasses import dataclass
from struct import pack


@dataclass
class AddToBookPacket:
    ip: str
    port: int

    @classmethod
    def from_bytes(cls, data: bytes):
        data = data.decode()
        if not ':' in data:
            return
        ip, port = data.split(':')
        if ip.count('.') != 3:
            return
        if not port.isdigit():
            return
        return cls(ip=ip, port=int(port))

    def to_tuple(self) -> tuple[str, int]:
        return (self.ip, self.port)

    def __str__(self):
        return f'{self.ip}:{self.port}'


address_book: list[AddToBookPacket] = []

server_socket = socket.socket()
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(('0.0.0.0', 9998))
server_socket.listen(3)
print("Listening for clients on", ('0.0.0.0', 9999))


def send_big(connection, data: str | bytes):
    if not isinstance(data, bytes):
        data = data.encode()
    data_length = pack('>Q', len(data))
    connection.sendall(data_length)
    connection.sendall(data)


def check_address_book_clients_alive():
    for address in address_book.copy():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        result = s.connect_ex(address.to_tuple())
        if result != 0:
            print(f"Remove", address, 'due to not alive with status =', result)
            address_book.remove(address)
        s.close()


def receive_clients():
    while True:
        client_socket, client_address = server_socket.accept()
        raw_packet = client_socket.recv(512)

        packet = AddToBookPacket.from_bytes(raw_packet)
        if packet is None:
            client_socket.send(b'Invalid addtobook packet')
            client_socket.close()
            continue
        
        if packet not in address_book:
            print(packet, "added to book")
            address_book.append(packet)

        check_address_book_clients_alive()
        address_book_dumped = ';'.join(map(str, address_book))
        print("sending", address_book_dumped)
        send_big(client_socket, address_book_dumped.encode())
        client_socket.close()


try:
    receive_clients()
except KeyboardInterrupt:
    print("Stopping seeder...")
    server_socket.close()

