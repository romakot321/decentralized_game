from dataclasses import dataclass, field
import datetime as dt
from hashlib import sha256
import json
from uuid import uuid4, UUID
from abc import abstractmethod, ABC
from utils import asdict


class StorableModel:
    @classmethod
    @property
    def table_name(cls):
        return cls.__name__


class TransactionData(ABC):
    ...


class Transaction(ABC, StorableModel):
    data: str
    actor: UUID
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
        return cls(nounce=nounce, timestamp=timestamp, previous_hash=prev_hash, transactions=transactions)

    def __str__(self):
        data = 'Block #{hash}\n\tCreated at: {timestamp}\n\tPrevious hash: {previous_hash}\n\t'.format(hash=self.hash, timestamp=self.timestamp, previous_hash=self.previous_hash)
        data += 'Transactions: ' + "\n\t\t".join(map(str, self.transactions))
        return data


@dataclass
class MoveTransactionData(TransactionData):
    bias: tuple[int, int]


@dataclass
class MoveTransaction(Transaction):
    data: str
    actor: UUID
    action: str = "move"

    @classmethod
    def pack_data(cls, data) -> str:
        if not isinstance(data, dict):
            data = asdict(data)
        return json.dumps(data)

    def unpack_data(self) -> MoveTransactionData:
        data_state = json.loads(self.data)
        return MoveTransactionData(**data_state)


@dataclass
class Actor(StorableModel):
    @staticmethod
    def new_id():
        return str(uuid4())

    id: str = field(default_factory=new_id)

