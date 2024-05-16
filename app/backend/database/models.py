from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import datetime as dt
from hashlib import sha256
from app.backend.utils import asdict
import json
from enum import Enum
import struct
from uuid import UUID

max_int64 = 0xFFFFFFFFFFFFFFFF


@dataclass
class StorableModel:
    @classmethod
    @property
    def table_name(cls):
        return cls.__name__

    def dump(self) -> bytes:
        """Serialize object to bytes for storing and transfer"""
        return ''.join([str(v) for k, v in self.__dict__.items()]).encode()

    @classmethod
    def undump(cls, rawdata: bytes) -> object:
        """Construct object from serialize bytes"""
        raise NotImplementedError


@dataclass
class Tip(StorableModel):
    value: str
    id: str = 'tip'


class TransactionsAction(Enum):
    MOVE = b'\x00'
    PICK = b'\x01'


class Transaction(ABC):
    TRANSACTION_DUMPED_SIZE = 64  # in bytes

    class TransactionData(ABC):
        ...

    data: str
    actor: str
    action: TransactionsAction

    @abstractmethod
    def unpack_data(self) -> TransactionData:
        ...

    @classmethod
    @abstractmethod
    def pack_data(cls, data) -> str:
        if not isinstance(data, dict):
            data = asdict(data)
        return json.dumps(data)

    @property
    def hash(self):
        return sha256(self.dump().encode()).hexdigest()

    @classmethod
    @property
    def table_name(cls) -> str:
        return 'Transaction'

    def __str__(self):
        return f'Transaction {self.action}, data = {self.data}, owner = {self.actor}'


@dataclass
class _BlockParent(StorableModel):
    transactions: list[Transaction]
    previous_hash: str
    timestamp: dt.datetime = field(default_factory=dt.datetime.now)
    nounce: int = 0
    id: str = field(init=False)
    hash: str = field(init=False)


class Block(_BlockParent):
    transactions: list[Transaction]
    previous_hash: str
    timestamp: dt.datetime = field(default_factory=dt.datetime.now)
    nounce: int = 0

    @property
    def hash(self):
        return sha256(f'{self.transactions}{self.previous_hash}{self.timestamp}{self.nounce}'.encode()).hexdigest()

    @property
    def id(self):
        return self.hash

    def __str__(self):
        data = 'Block #{hash}\n\tCreated at: {timestamp}\n\tPrevious hash: {previous_hash}\n\t'.format(hash=self.hash, timestamp=self.timestamp, previous_hash=self.previous_hash)
        data += 'Transactions: ' + "\n\t\t".join(map(str, self.transactions))
        return data


@dataclass
class MoveTransaction(Transaction):
    @dataclass
    class TransactionData(Transaction.TransactionData):
        bias: tuple[int, int]

    data: bytes
    actor: str
    action: bytes = TransactionsAction.MOVE.value

    @classmethod
    def pack_data(cls, data: tuple[int, int] | TransactionData) -> bytes:
        if isinstance(data, cls.TransactionData):
            data = data.bias
        return struct.pack('>ii', data[0], data[1])

    def unpack_data(self) -> TransactionData:
        return self.TransactionData(
            bias=struct.unpack('>ii', self.data)
        )


@dataclass
class PickTransaction(Transaction):
    @dataclass
    class TransactionData(Transaction.TransactionData):
        pick_position: tuple[int, int]
        object_id: int

    data: bytes
    actor: str
    action: bytes = TransactionsAction.PICK.value

    @classmethod
    def pack_data(cls, data: TransactionData | tuple[tuple, int]) -> bytes:
        if isinstance(data, tuple):
            data = cls.TransactionData(pick_position=data[0], object_id=data[1])
        object_int_id = UUID(data.object_id).int
        object_part1 = (object_int_id >> 64) & max_int64
        object_part2 = object_int_id & max_int64

        return struct.pack('>iiQQ', data.pick_position[0], data.pick_position[1], object_part1, object_part2)

    def unpack_data(self) -> TransactionData:
        x, y, object_part1, object_part2 = struct.unpack('>iiQQ', self.data)
        object_int_id = (object_part1 << 64) | object_part2
        object_id = str(UUID(int=object_int_id))
        return PickTransaction.TransactionData(
            pick_position=(x, y),
            object_id=object_id
        )


_action_to_transaction_class = {
    TransactionsAction.MOVE: MoveTransaction,
    TransactionsAction.PICK: PickTransaction,
    TransactionsAction.MOVE.value: MoveTransaction,
    TransactionsAction.PICK.value: PickTransaction,
}
