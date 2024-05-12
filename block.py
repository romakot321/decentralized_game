from models import Block, Transaction, StorableModel
from utils import asdict
from dataclasses import dataclass


@dataclass
class Tip(StorableModel):
    value: str
    id: str = 'tip'


class BlockRepository:
    def __init__(self, db_service):
        self.db_service = db_service

    def mine(self, block: Block):
        while not block.hash.startswith('00'):
            block.nounce += 1
        return block

    def make(self, transactions: list[Transaction]) -> Block:
        last_block = self.get_last()
        prev_hash = '' if last_block is None else last_block.hash
        new_block = Block(
            transactions=transactions,
            previous_hash=prev_hash
        )
        new_block = self.mine(new_block)
        return new_block

    def store(self, block: Block) -> int:
        self.db_service.save(Tip(value=block.hash))
        return self.db_service.save(block)

    def get_last(self) -> Block | None:
        last_hash = self.db_service.get(Tip.table_name, 'tip')
        if last_hash:
            return self.get_one(last_hash.value)

    def get_one(self, block_hash) -> Block | None:
        return self.db_service.get(Block.table_name, block_hash)

    def get_many(self, **filters) -> list[Block]:
        res = self.db_service.find(Block.table_name, **filters)
        return res

    def iterate_blocks(self, stop_hash: str | None = None) -> Block:
        curr_block = self.get_last()

        while curr_block is not None and curr_block.previous_hash != '' and curr_block.previous_hash != stop_hash:
            yield curr_block
            curr_block = self.get_one(curr_block.previous_hash)

    def update_chain(self, dumped_data: list[str]):
        for block in self.iterate_blocks():
            self.db_service.delete(Block.table_name, block.hash)

        for data in dumped_data[::-1]:
            block = Block.undump(data)
            self.store(block)

    def validate_new_transaction(self, transaction) -> bool:
        return True

    def add_received_block(self, dumped_data: str):
        block = Block.undump(dumped_data)
        tip_block = self.get_last()
        if tip_block.hash != block.previous_hash:
            print("!!!Received invalid block!!!")
            return
        self.store(block)

