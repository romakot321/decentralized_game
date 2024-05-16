from app.backend.network.models import Request
from app.backend.network.models import GetBlocksRequest
from app.backend.network.models import GetAddressBookRequest
from app.backend.network.models import PublishBlockRequest
from app.backend.network.models import NetworkBlock
from app.backend.network.models import PacketType
from app.backend.network.serializers import pack_block, unpack_block

from app.backend.utils import asdict

import ipaddress
import struct


class RequestFactory:
    def __init__(self, database_repository):
        self.db_rep = database_repository

    def make_get_blocks(self) -> GetBlocksRequest:
        return GetBlocksRequest(packed=struct.pack('>c', PacketType.GET_BLOCKS.value))

    def make_get_address_book(self, body: tuple | bytes) -> GetAddressBookRequest:
        if isinstance(body, tuple):
            packed = struct.pack(
                '>cIH',
                GetAddressBookRequest.type.value,
                int(ipaddress.IPv4Address(body[0])),
                body[1]
            )
        elif isinstance(body, bytes):
            packed = body
            _, ip, port = struct.unpack('>cIH', body)
            body = (str(ipaddress.ip_address(ip)), port)
        return GetAddressBookRequest(body=body, packed=packed)

    def make_publish_block(self, body: NetworkBlock | bytes) -> PublishBlockRequest:
        if isinstance(body, bytes):
            packed = body
            body = unpack_block(body[1:])
        else:
            body_packed = pack_block(body)
            packed = struct.pack(f'>c{len(body_packed)}s', PacketType.PUBLISH_BLOCK.value, body_packed)
        return PublishBlockRequest(body=body, packed=packed)

    def undump(self, raw_request: bytes) -> Request | None:
        if not raw_request:
            return
        request_type = raw_request[:1]
        if request_type == PacketType.GET_BLOCKS.value:
            return self.make_get_blocks()
        if request_type == PacketType.GET_ADDRESS_BOOK.value:
            return self.make_get_address_book(raw_request)
        if request_type == PacketType.PUBLISH_BLOCK.value:
            return self.make_publish_block(raw_request)

    def handle_request(self, request: Request):
        if request.type == PublishBlockRequest.type:
            block = self.db_rep.make_block(**asdict(request.body))
            self.db_rep.store_block(block)

