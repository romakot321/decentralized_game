from backend.utils import asdict
from backend.database.models import Tip, Block, Transaction, StorableModel


class BlockRepository:
    def __init__(self, db_service, transaction_repository):
        self.db_service = db_service
        self.trans_rep = transaction_repository

    def generate(self):
        transactions = self.trans_rep.get_many()
        self.trans_rep.clear()
        block = self.make(transactions)
        return block

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

    def validate_transaction(self, transaction: Transaction):
        return True

    def validate_block(self, block: Block):
        tip_block = self.get_last()
        if not tip_block:
            return True
        return tip_block.hash == block.previous_hash and \
                all(self.validate_transaction(tr) for tr in block.transactions)

    def store(self, block: Block) -> int | None:
        if not self.validate_block(block):
            return
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

    def replace_chain(self, chain: list[Block]):
        for block in self.get_many():
            self.db_service.delete(Block.table_name, block.hash)
        print(self.get_many())

        [self.store(block) for block in chain]

