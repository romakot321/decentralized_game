from dataclasses import dataclass
from enum import Enum
from typing import Any
import struct
import ipaddress
from typing import Any
import datetime as dt


class PacketType(Enum):
    GET_BLOCKS = b'\x00'
    GET_ADDRESS_BOOK = b'\x01'
    PUBLISH_TRANSACTION = b'\x02'
    PUBLISH_BLOCK = b'\x03'


@dataclass
class NetworkTransaction:
    action: bytes
    data: bytes
    actor: str  # UUID


@dataclass
class NetworkBlock:
    transactions: list[NetworkTransaction]
    previous_hash: str
    timestamp: dt.datetime
    nounce: int


@dataclass
class Request:
    packed: bytes
    body: Any
    type: PacketType
    have_response: bool


@dataclass
class GetAddressBookRequest(Request):
    body: tuple[str, int]
    type: PacketType = PacketType.GET_ADDRESS_BOOK
    have_response: bool = True


@dataclass
class GetBlocksRequest(Request):
    body: None = None
    type: PacketType = PacketType.GET_BLOCKS
    have_response: bool = True


@dataclass
class PublishBlockRequest(Request):
    body: NetworkBlock
    type: PacketType = PacketType.PUBLISH_BLOCK
    have_response: bool = False


class RequestPublicTransaction(Request):
    pass


@dataclass
class Response:
    body: Any
    type: PacketType


@dataclass
class GetBlocksResponse(Response):
    body: list[NetworkBlock]
    type: PacketType = PacketType.GET_BLOCKS


@dataclass
class GetAddressBookResponse(Response):
    body: list[tuple[str, int]]
    type: PacketType = PacketType.GET_ADDRESS_BOOK

