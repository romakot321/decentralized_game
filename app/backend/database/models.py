import datetime as dt
from hashlib import sha256
from uuid import UUID
from app.backend.utils import asdict
from dataclasses import dataclass, field

max_int64 = 0xFFFFFFFFFFFFFFFF


@dataclass
class StorableModel:
    @classmethod
    @property
    def table_name(cls):
        return cls.__name__.lower()

    def dump(self) -> bytes:
        """Serialize object to bytes for storing and transfer"""
        return ''.join([str(v) for k, v in self.__dict__.items()]).encode()

    @classmethod
    def undump(cls, rawdata: bytes) -> object:
        """Construct object from serialize bytes"""
        raise NotImplementedError


@dataclass
class TXInput:
    tx_id: str
    output_index: int
    unlock_script: bytes

    def __str__(self):
        return f'Input. TX id={self.tx_id} Output={self.output_index}'


@dataclass
class TXOutput:
    input_index: int
    lock_script: bytes
    value: bytes

    def __str__(self):
        return f'Output. Input={self.input_index} Value={self.value}'


@dataclass
class Transaction(StorableModel):
    inputs: list[TXInput]
    outputs: list[TXOutput]

    def encode(self):  # TODO change
        return sha256(f'{self.inputs}{self.outputs}'.encode()).digest()

    @property
    def id(self) -> str:
        return sha256(sha256(self.encode()).digest()).hexdigest()

    @classmethod
    def from_network_model(cls, model):
        return Transaction(
            inputs=[TXInput(**inp.model_dump()) for inp in model.inputs],
            outputs=[TXOutput(**out.model_dump()) for out in model.outputs]
        )

    def __str__(self):
        return f'Transaction #{self.id}\n\tInputs: {[str(i) for i in self.inputs]}\n\tOutputs: {[str(o) for o in self.outputs]}'


@dataclass
class UTXOs(StorableModel):
    transaction_id: str
    outputs_indexes: list[int]
    transaction: Transaction


@dataclass
class Tip(StorableModel):
    value: str
    id: str = 'tip'


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

    @classmethod
    def from_network_model(cls, model):
        txs = []
        for tx in model.transactions:
            tx = Transaction(
                inputs=[TXInput(**inp.model_dump()) for inp in tx.inputs],
                outputs=[TXOutput(**out.model_dump()) for out in tx.outputs]
            )
            txs.append(tx)
        prev_hash = '' if model.prev_hash == '\x00' * 64 else model.prev_hash
        return cls(
            transactions=txs,
            previous_hash=prev_hash,
            timestamp=model.timestamp,
            nounce=model.nounce
        )

    def __str__(self):
        data = 'Block #{hash}\n\tCreated at: {timestamp}\n\tPrevious hash: {previous_hash}\n\t'.format(hash=self.hash, timestamp=self.timestamp, previous_hash=self.previous_hash)
        data += 'Transactions: ' + "\n\t\t".join(map(str, self.transactions))
        return data


class ValidateError(Exception):
    pass

