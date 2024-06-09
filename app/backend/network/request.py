from app.backend.network.models import Message, Command
from app.backend.network.models import NodesStorePayload, BlocksPayload
from app.backend.network.models import GetBlocksPayload
from app.backend.network.models import NetworkBlock, NetworkTransaction, NetworkTXInput, NetworkTXOutput
from app.backend.network.models import TransactionsPayload

from app.backend.utils import asdict
from app.backend.database.models import ValidateError, Block

import datetime as dt


class RequestWorker:
    def __init__(
            self,
            database_repository,
            nodes_store
    ):
        self.db_rep = database_repository
        self.nodes_store = nodes_store

    def get_blocks(self, request_payload: bytes):
        request_payload = GetBlocksPayload.decode(request_payload)
        k = 0
        blocks = []
        iterator = self.db_rep.iterate_blocks()
        while k < request_payload.count:
            try:
                block = next(iterator)
            except StopIteration:
                break
            blocks.append(NetworkBlock.from_db_model(block))
            if blocks[-1].prev_hash == '':
                break
        return blocks

    def add_blocks(self, request_payload: bytes) -> bool:
        request_payload = BlocksPayload.decode(request_payload)
        for block in request_payload.blocks:
            block = Block.from_network_model(block)
            try:
                self.db_rep.store_block(block)
            except ValidateError:
                return False
        return True

    def add_transactions(self, request_payload: bytes) -> bool:
        request_payload = TransactionsPayload.decode(request_payload)
        for tx in request_payload.transactions:
            try:
                self.db_rep.store_transaction(tx)
            except ValidateError:
                return False
        return True

    def handle(self, data: bytes) -> Message:
        msg = Message.from_bytes(data)
        self.nodes_store.store(msg.sender)
        print("GET", msg.command)
        match msg.command:
            case Command.get_nodes_store:
                payload = NodesStorePayload(
                    nodes=self.nodes_store.get()
                )
                return Message(
                    command=Command.nodes_store,
                    payload=payload.encode()
                )
            case Command.get_blocks:
                payload = BlocksPayload(
                    blocks=self.get_blocks(msg.payload)
                )
                return Message(
                    command=Command.blocks,
                    payload=payload.encode()
                )
            case Command.blocks:
                status = self.add_blocks(msg.payload)
                if not status:
                    return Message(command=Command.error, payload=b'Invalid blocks')
                return Message(command=Command.error, payload=b'OK')
            case Command.transactions:
                status = self.add_transactions(msg.payload)
                if not status:
                    return Message(command=Command.error, payload=b'Invalid transactions')
                return Message(command=Command.error, payload=b'OK')
        return Message(
            command=Command.error,
            payload=b'Unknown command'
        )
