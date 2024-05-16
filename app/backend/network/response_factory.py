from app.backend.network.models import Request, NetworkBlock
from app.backend.network.models import GetBlocksResponse
from app.backend.network.models import GetAddressBookResponse
from app.backend.network.models import PacketType
from app.backend.network.serializers import unpack_block, pack_block
import struct
import ipaddress

address_size = struct.calcsize('>IH')


class ResponseFactory:
    def __init__(self, database_repository):
        self.db_rep = database_repository

    def make_response_from_request(self, request: Request) -> bytes:
        if request.type == PacketType.GET_BLOCKS:
            return self._make_get_blocks_response_from_request()

    def _make_get_blocks_response_from_request(self) -> bytes:
        dumped_blocks = [pack_block(block) for block in self.db_rep.iterate_blocks()]
        response = b''.join([
            struct.pack(f'>Q{len(block)}s', len(block), block)
            for block in dumped_blocks
        ])
        return response

    def _make_get_blocks_response_from_bytes(self, rawdata: bytes) -> list[NetworkBlock]:
        blocks = []
        while rawdata:
            (block_size,) = struct.unpack('>Q', rawdata[:8])
            block = unpack_block(rawdata[8:8 + block_size])
            blocks.append(block)
            rawdata = rawdata[8 + block_size:]
        return blocks

    def make_get_blocks(self, rawdata: bytes) -> GetBlocksResponse:
        blocks = self._make_get_blocks_response_from_bytes(rawdata)
        return GetBlocksResponse(body=blocks)

    def _make_get_address_book_resp_from_bytes(self, rawdata: bytes) -> list[tuple]:
        book = []
        while rawdata:
            ip_int, port = struct.unpack('>IH', rawdata[:address_size])
            book.append((str(ipaddress.ip_address(ip_int)), port))
            rawdata = rawdata[address_size:]
        return book

    def make_get_address_book(self, rawdata: bytes) -> GetAddressBookResponse:
        address_book = self._make_get_address_book_resp_from_bytes(rawdata)
        return GetAddressBookResponse(body=address_book)

