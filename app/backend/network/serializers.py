import struct
from uuid import UUID
import datetime as dt
from app.backend.network.models import NetworkBlock, NetworkTransaction

max_int64 = 0xFFFFFFFFFFFFFFFF
transaction_info_size = struct.calcsize('>cQQ')
block_info_size = struct.calcsize('>Qd32s')


def unpack_transaction(rawdata: bytes) -> NetworkTransaction:
    data_size = len(rawdata) - transaction_info_size
    action, actor_part1, actor_part2, data = struct.unpack(f'>cQQ{data_size}s', rawdata)
    actor_int = (actor_part1 << 64) | actor_part2
    actor = str(UUID(int=actor_int))
    return NetworkTransaction(
        action=action,
        data=data,
        actor=actor
    )


def pack_transaction(transaction: NetworkTransaction) -> bytes:
    actor_int_id = UUID(transaction.actor).int
    actor_part1 = (actor_int_id >> 64) & max_int64
    actor_part2 = actor_int_id & max_int64
    rawdata = struct.pack(
        f'>cQQ{len(transaction.data)}s',
        transaction.action,
        actor_part1,
        actor_part2,
        transaction.data
    )
    return rawdata


def pack_block(block: NetworkBlock) -> bytes:
    info = (
        block.nounce,
        block.timestamp.timestamp(),
        bytes.fromhex(block.previous_hash)
    )
    
    transactions_packed = b'\xde\xad'.join([
        pack_transaction(tr)
        for tr in block.transactions
    ])

    rawdata = struct.pack(f'>Qd32s{len(transactions_packed)}s', *info, transactions_packed)
    return rawdata


def unpack_block(rawdata: bytes) -> NetworkBlock:
    transactions_data_size = len(rawdata) - block_info_size
    transactions = []
    nounce, timestamp, prev_hash, trans_data = struct.unpack(f'>Qd32s{transactions_data_size}s', rawdata)

    timestamp = dt.datetime.fromtimestamp(timestamp)
    prev_hash = format(int.from_bytes(prev_hash), 'x').rjust(64, '0')
    if prev_hash == '0' * 64:
        prev_hash = ''
    if trans_data:
        transactions = [unpack_transaction(tr) for tr in trans_data.split(b'\xde\xad')]

    return NetworkBlock(
        transactions=transactions,
        previous_hash=prev_hash,
        timestamp=timestamp,
        nounce=nounce
    )

