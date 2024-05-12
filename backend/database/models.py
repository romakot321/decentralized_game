from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import datetime as dt
from hashlib import sha256
from backend.utils import asdict
import json
from enum import Enum


@dataclass
class StorableModel:
    @classmethod
    @property
    def table_name(cls):
        return cls.__name__


@dataclass
class Tip(StorableModel):
    value: str
    id: str = 'tip'


class TransactionsAction(Enum):
    MOVE = 'move'
    PICK = 'pick'


class Transaction(ABC):
    class TransactionData(ABC):
        ...

    data: str
    actor: str
    action: str

    @abstractmethod
    def unpack_data(self) -> TransactionData:
        ...

    @classmethod
    @abstractmethod
    def pack_data(cls, data) -> str:
        if not isinstance(data, dict):
            data = asdict(data)
        return json.dumps(data)

    def dump(self):
        return '||'.join([self.data, str(self.actor), self.action])

    @classmethod
    def undump(cls, data):
        if not data:
            return
        data, actor, action = data.split('||')
        return cls(data=data, actor=actor, action=action)

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
        return sha256(self.dump().encode()).hexdigest()

    @property
    def id(self):
        return self.hash

    def dump(self) -> str:
        data = ';;'.join([
            str(self.nounce),
            str(self.timestamp),
            str(self.previous_hash),
            '&&'.join([tr.dump() for tr in self.transactions])
        ])
        return data

    @classmethod
    def undump(cls, data: str):
        nounce, timestamp, prev_hash, transactions = data.split(';;')
        transactions = [MoveTransaction.undump(i) for i in transactions.split('&&')]
        if transactions == [None]:
            transactions = []
        transactions = [_action_to_transaction_class.get(TransactionsAction(tr.action))(**asdict(tr)) for tr in transactions]
        return cls(nounce=nounce, timestamp=timestamp, previous_hash=prev_hash, transactions=transactions)

    def __str__(self):
        data = 'Block #{hash}\n\tCreated at: {timestamp}\n\tPrevious hash: {previous_hash}\n\t'.format(hash=self.hash, timestamp=self.timestamp, previous_hash=self.previous_hash)
        data += 'Transactions: ' + "\n\t\t".join(map(str, self.transactions))
        return data


@dataclass
class MoveTransaction(Transaction):
    @dataclass
    class TransactionData(Transaction.TransactionData):
        bias: tuple[int, int]

    data: str
    actor: str
    action: str = "move"

    @classmethod
    def pack_data(cls, data) -> str:
        if isinstance(data, cls.TransactionData):
            data = asdict(data)
        elif isinstance(data, tuple):
            data = asdict(cls.TransactionData(bias=data))
        return json.dumps(data)

    def unpack_data(self) -> TransactionData:
        data_state = json.loads(self.data)
        return self.TransactionData(**data_state)


@dataclass
class PickTransaction(Transaction):
    @dataclass
    class TransactionData(Transaction.TransactionData):
        pick_position: tuple[int, int]
        object_id: str

    data: str
    actor: str
    action: str = "pick"

    @classmethod
    def pack_data(cls, data) -> str:
        if isinstance(data, cls.TransactionData):
            data = asdict(data)
        elif isinstance(data, dict):
            data = asdict(cls.TransactionData(**data))
        return json.dumps(data)

    def unpack_data(self) -> TransactionData:
        data_state = json.loads(self.data)
        return PickTransaction.TransactionData(**data_state)


_action_to_transaction_class = {
    TransactionsAction.MOVE: MoveTransaction,
    TransactionsAction.PICK: PickTransaction
}
