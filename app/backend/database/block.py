from app.backend.utils import asdict
from app.backend.database.models import Tip, Block, Transaction, StorableModel
import datetime as dt


class BlockService:
    def __init__(self, db_service):
        self.db_service = db_service

    def mine(self, block: Block):
        while not block.hash.startswith('00'):
            block.nounce += 1
        return block

    def make(self, transactions: list[Transaction], prev_hash, timestamp, nounce) -> Block:
        if prev_hash is None:
            last_block = self.get_last()
            prev_hash = '' if last_block is None else last_block.hash
        if timestamp is None:
            timestamp = dt.datetime.now(dt.UTC)
        new_block = Block(
            transactions=transactions,
            previous_hash=prev_hash,
            timestamp=timestamp,
            nounce=(nounce if nounce else 0)
        )
        new_block = self.mine(new_block)
        return new_block

    def validate_block(self, block: Block):
        """validate block with already validated transaction"""
        tip_block = self.get_last()
        if not tip_block:
            return True
        return tip_block.hash == block.previous_hash

    def store(self, block: Block) -> int | None:
        if not self.validate_block(block):
            return
        self.db_service.save(Tip(value=block.hash))
        return self.db_service.save(block)

    def get_last(self) -> Block | None:
        last_hash = self.db_service.get(Tip.table_name, 'tip')
        if last_hash:
            return self.get_one(last_hash.value)

    def iterate_blocks(self, stop_hash: str | None = None) -> Block:
        curr_block = self.get_last()
        if stop_hash is None:
            stop_hash = ''

        while curr_block is not None and curr_block.hash != stop_hash:
            yield curr_block
            curr_block = self.get_one(curr_block.previous_hash)

    def get_one(self, block_hash) -> Block | None:
        return self.db_service.get(Block.table_name, block_hash)

    def get_many(self, **filters) -> list[Block]:
        res = self.db_service.find(Block.table_name, **filters)
        return res

    def append_chain(self, new_chain: list[Block]):
        for block in self.get_many():
            self.db_service.delete(Block.table_name, block.hash)

        [self.store(block) for block in new_chain[::-1]]
        print('chain', *new_chain, sep='\n')

