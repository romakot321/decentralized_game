from app.backend.network.connection import ConnectionService
from app.backend.network.store import NodesStore
from app.backend.network.models import Message, Command, Payload
from app.backend.network.models import NodesStorePayload, GetBlocksPayload
from app.backend.network.models import BlocksPayload
from app.backend.network.models import Node

from threading import Thread


class NodeService:
    def __init__(
            self,
            bind_address: tuple,
            nodes_store,
            request_worker,
            response_worker
    ):
        self.bind_address = bind_address
        self.nodes_store = nodes_store
        self.request_worker = request_worker
        self.response_worker = response_worker

        self.sender = Node(ip=self.bind_address[0], port=self.bind_address[1])
        self.server_connection = None

    def init(self):
        self.server_connection = ConnectionService(
            bind_address=self.bind_address
        )
        self.server_connection.init()
        Thread(target=self._accept_requests).start()

    def make_message(self, command, payload=None) -> Message:
        if payload is None:
            payload = b''
        return Message(command=command, sender=self.sender, payload=payload)

    def _accept_requests(self):
        while True:
            request = self.server_connection.receive()
            if request is None:
                continue
            response = self._handle_request(request.body)
            self.server_connection.answer(response.model_dump())
            self.server_connection.close()

    def _handle_request(self, data: bytes) -> Message:
        msg = self.request_worker.handle(data)
        msg.sender = self.sender
        return msg

    def _handle_response(self, data: bytes) -> Payload | None:
        return self.response_worker.handle(data)

    def _do_request(self, msg: Message, node) -> Payload | None:
        conn = ConnectionService(connect_address=(str(node.ip), node.port))
        conn.init()
        conn.answer(msg.model_dump())
        response = conn.receive()
        conn.close()
        if response is None:
            return
        self.nodes_store.store((str(node.ip), node.port))
        return self._handle_response(response.body)

    def do_direct_request(self, msg: Message, address: tuple) -> Payload | None:
        node = Node(ip=address[0], port=address[1])
        return self._do_request(msg, node)

    def do_broadcast_request(self, msg) -> list[Payload]:
        responses = []
        for node in self.nodes_store.get():
            if node == self.sender:
                continue
            responses.append(self._do_request(msg, node))
        return [resp for resp in responses if resp is not None]

    def store_node(self, node: Node):
        self.nodes_store.store((str(node.ip), node.port))

if __name__ == '__main__':
    n1 = NodeService(NodesStore(), ('127.0.0.1', 10000))
    n1.init()
    n2 = NodeService(NodesStore(), ('127.0.0.1', 10001))
    n2.init()
    resp = n2._do_request(
        Message(
            command=Command.get_nodes_store,
            payload=b''
        ),
        Node(ip='127.0.0.1', port=10000)
    )

