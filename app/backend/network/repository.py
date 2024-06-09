from app.backend.network.models import Message, Command
from app.backend.network.models import GetBlocksPayload, BlocksPayload
from app.backend.network.models import TransactionsPayload
from app.backend.network.models import NetworkBlock, NetworkTransaction


class NetworkRepository:
    def __init__(self, node_service):
        self.node_service = node_service

    def init(self):
        self.node_service.init()

    def update_nodes_store(self, seeder_address: tuple):
        msg = self.node_service.make_message(command=Command.get_nodes_store)
        response = self.node_service.do_direct_request(msg, seeder_address)
        if not response:
            return
        for node in response.nodes:
            self.node_service.store_node(node)
        return response

    def request_blocks(self) -> list[list[NetworkBlock]]:
        msg = self.node_service.make_message(
            command=Command.get_blocks,
            payload=GetBlocksPayload().encode()
        )
        responses = self.node_service.do_broadcast_request(msg)
        return [resp.blocks for resp in responses]

    def relay_block(self, block: NetworkBlock) -> list[Message]:
        msg = self.node_service.make_message(
            command=Command.blocks,
            payload=BlocksPayload(blocks=[block]).encode()
        )
        responses = self.node_service.do_broadcast_request(msg)
        return responses

    def relay_transaction(self, transaction: NetworkTransaction) -> list[Message]:
        msg = self.node_service.make_message(
            command=Command.transactions,
            payload=TransactionsPayload(transactions=[transaction]).encode()
        )
        responses = self.node_service.do_broadcast_request(msg)
        return responses


if __name__ == '__main__':
    from app.backend.network.node import NodeService
    from app.backend.network.request import RequestWorker
    from app.backend.network.response import ResponseWorker
    from app.backend.network.store import NodesStore

    ns1 = NodesStore()
    r1 = NetworkRepository(
        NodeService(
            bind_address=('127.0.0.1', 10000),
            nodes_store=ns1,
            request_worker=RequestWorker(None, ns1),
            response_worker=ResponseWorker()
        )
    )
    ns2 = NodesStore()
    r2 = NetworkRepository(
        NodeService(
            bind_address=('127.0.0.1', 10001),
            nodes_store=ns2,
            request_worker=RequestWorker(None, ns2),
            response_worker=ResponseWorker()
        )
    )
    r1.init()
    r2.init()

    r1.update_nodes_store(r2.node_service.bind_address)
    r1.relay_block(r1.node_service.request_worker._blocks[0])
    r1.relay_transaction(r1.node_service.request_worker._blocks[0].transactions[0])
