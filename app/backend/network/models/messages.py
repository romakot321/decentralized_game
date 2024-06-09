from pydantic import BaseModel, model_validator, model_serializer
from pydantic import Field
from hashlib import sha256
from enum import Enum
import struct

from app.backend.network.models import Node, NetworkBlock, NetworkTransaction


class Command(Enum):
    get_nodes_store = 0
    nodes_store = 1
    get_blocks = 2
    blocks = 3
    transactions = 4
    error = 5


class Message(BaseModel):
    command: Command
    sender: Node = None
    payload: bytes = b''

    @property
    def checksum(self) -> bytes:
        return sha256(self.payload).digest()[:4]

    @property
    def payload_size(self) -> int:
        return len(self.payload)

    @model_validator(mode='before')
    @classmethod
    def from_bytes(cls, data: bytes):
        if isinstance(data, dict):
            return data
        header = data[:struct.calcsize(f'>H4s{Node._HEADER_SIZE.default}sQ')]
        payload = data[len(header):]
        cmd, checksum, sender, size = struct.unpack(f'>H4s{Node._HEADER_SIZE.default}sQ', header)
        assert len(payload) == size, "Invalid payload size"
        sender = Node.decode(sender)
        message = cls(command=Command(cmd), sender=sender, payload=payload)
        assert message.checksum == checksum, f'Invalid message checksum {checksum}=={message.checksum}'
        return message

    @model_serializer
    def encode(self) -> bytes:
        data = struct.pack(
            f'>H4s{Node._HEADER_SIZE.default}sQ{self.payload_size}s',
            self.command.value,
            self.checksum,
            self.sender.encode(),
            self.payload_size,
            self.payload
        )
        return data


class Payload(BaseModel):
    def encode(self) -> bytes:
        raise NotImplementedError

    @classmethod
    def decode(cls, data):
        raise NotImplementedError


class NodesStorePayload(Payload):
    nodes: list[Node]

    def encode(self) -> bytes:
        return b''.join(map(lambda i: i.encode(), self.nodes))

    @model_validator(mode='before')
    @classmethod
    def decode(cls, data: bytes | dict):
        if isinstance(data, dict):
            return data
        nodes = [Node.decode(data[i:i + Node._HEADER_SIZE.default]) for i in range(0, len(data), Node._HEADER_SIZE.default)]
        return cls(nodes=nodes)


class GetBlocksPayload(Payload):
    offset: int = 0
    count: int = Field(le=500, default=500)
    only_headers: bool = False

    @model_serializer
    def encode(self) -> bytes:
        return struct.pack('>QH?', self.offset, self.count, self.only_headers)

    @model_validator(mode='before')
    @classmethod
    def decode(cls, data: bytes | dict):
        if isinstance(data, dict):
            return data
        offset, count, only_headers = struct.unpack('>QH?', data)
        return cls(offset=offset, count=count, only_headers=only_headers)


class BlocksPayload(Payload):
    blocks: list[NetworkBlock]

    @model_serializer
    def encode(self) -> bytes:
        return b''.join([block.encode() for block in self.blocks])

    @model_validator(mode='before')
    @classmethod
    def decode(cls, data: bytes | dict):
        if isinstance(data, dict):
            return data
        blocks = []
        i = 0
        while i < len(data):
            _, _, _, txs_size = struct.unpack('>dQ64sQ', data[i:i + NetworkBlock._HEADER_SIZE.default])
            block_size = NetworkBlock._HEADER_SIZE.default + txs_size
            blocks.append(NetworkBlock.decode(data[i:i + block_size]))
            i += block_size
        return cls(blocks=blocks)


class TransactionsPayload(Payload):
    transactions: list[NetworkTransaction]

    @model_serializer
    def encode(self) -> bytes:
        return b''.join([tx.encode() for tx in self.transactions])

    @model_validator(mode='before')
    @classmethod
    def decode(cls, data: bytes | dict):
        if isinstance(data, dict):
            return data
        txs = []
        i = 0
        tx_header = NetworkTransaction._HEADER_SIZE.default
        while i < len(data):
            (outputs_size,) = struct.unpack('>Q', data[i:i + tx_header])
            (inputs_size,) = struct.unpack(
                '>Q',
                data[
                    i + tx_header + outputs_size
                    :
                    i + tx_header * 2 + outputs_size
                ]
            )
            txs.append(NetworkTransaction.decode(data[i:i + tx_header * 2 + outputs_size + inputs_size]))
            i += tx_header * 2 + outputs_size + inputs_size
        return cls(transactions=txs)

