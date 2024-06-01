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
    tx_id: int
    output_index: int
    unlock_script: bytes


@dataclass
class TXOutput:
    input_index: int
    lock_script: bytes
    value: bytes


@dataclass
class Transaction(StorableModel):
    inputs: list[TXInput]
    outputs: list[TXOutput]

    def encode(self):  # TODO change
        return sha256(f'{self.inputs}{self.outputs}'.encode()).digest()

    @property
    def id(self) -> str:
        return sha256(sha256(self.encode()).digest()).hexdigest()


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

    def __str__(self):
        data = 'Block #{hash}\n\tCreated at: {timestamp}\n\tPrevious hash: {previous_hash}\n\t'.format(hash=self.hash, timestamp=self.timestamp, previous_hash=self.previous_hash)
        data += 'Transactions: ' + "\n\t\t".join(map(str, self.transactions))
        return data


class ValidateError(Exception):
    pass

