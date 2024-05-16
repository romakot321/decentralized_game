from app.backend.database.models import Block
from app.backend.database.models import Transaction
import datetime as dt


class DatabaseRepository:
    def __init__(self, block_service, transaction_service):
        self.block_service = block_service
        self.trans_service = transaction_service

    def iterate_blocks(self, stop_hash: str | None = None):
        return self.block_service.iterate_blocks(stop_hash)

    def make_block(
            self,
            transactions: list[Transaction | dict],
            previous_hash: str | None = None,
            timestamp: dt.datetime | None = None,
            nounce: int | None = None
    ) -> Block:
        transactions = [(self.trans_service.make(**tr) if isinstance(tr, dict) else tr) for tr in transactions]
        return self.block_service.make(transactions, previous_hash, timestamp, nounce)

    def generate_block(self) -> Block:
        """Get transactions from pool and make block"""
        transactions = self.trans_service.get_many()
        self.trans_service.clear()
        block = self.make_block(transactions)
        return block

    def store_block(self, block: Block):
        self.block_service.store(block)

