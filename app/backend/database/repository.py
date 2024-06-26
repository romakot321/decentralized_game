from app.backend.database.models import Block
from app.backend.database.models import Transaction
from app.backend.database.models import TXOutput, TXInput, UTXOs
from app.backend.database.models import ValidateError
from app.backend.database.models import Key
import datetime as dt
from uuid import uuid4


class DatabaseRepository:
    def __init__(self, block_service, transaction_service, key_service):
        self.block_service = block_service
        self.tx_service = transaction_service
        self.key_service = key_service

        self._token_to_key: dict[str, Key] = {}

    def iterate_blocks(self, stop_hash: str | None = None):
        return self.block_service.iterate_blocks(stop_hash)

    def find_utxos(
            self,
            transaction_id: str = None,
            output_index: int = None,
            output_lock_script_part: bytes = None,
            output_value: bytes = None
    ) -> list[UTXOs]:
        return self.tx_service.get_utxos(
            transaction_id,
            output_index,
            output_lock_script_part,
            output_value
        )

    def make_transaction(self, inputs: list[TXInput], outputs: list[TXOutput]) -> Transaction:
        return self.tx_service.make(inputs=inputs, outputs=outputs)

    def make_transaction_output(self, input_index, value: bytes, lock_script: bytes = None, receiver_address: bytes = None):
        return self.tx_service.make_output(input_index, value, lock_script, receiver_address)

    def make_transaction_input(self, tx_id, output_index, unlock_script: bytes = None, key: Key = None):
        return self.tx_service.make_input(tx_id, output_index, unlock_script, key)

    def make_block(
            self,
            transactions: list[Transaction | dict],
            previous_hash: str | None = None,
            timestamp: dt.datetime | None = None,
            nounce: int | None = None
    ) -> Block:
        transactions = [(self.tx_service.make(**tr) if isinstance(tr, dict) else tr) for tr in transactions]
        return self.block_service.make(transactions, previous_hash, timestamp, nounce)

    def generate_block(self) -> Block:
        """Pop transactions from pool and make block"""
        transactions = self.tx_service.pop_all()
        block = self.make_block(transactions)
        return block

    def store_transaction(self, transaction: Transaction):
        """Push transaction to pool"""
        self.tx_service.store(transaction)
        self.tx_service.create_utxos(transaction)

    def _validate_transactions(self, txs: list):
        for tx in txs:
            self.tx_service.delete(tx)
        for tx in txs:
            if not self.tx_service.validate(tx):
                raise ValidateError("Invalid transactions in block")
            self.tx_service.create_utxos(tx)

    def store_block(self, block: Block, validate_transactions: bool = True):
        if validate_transactions and block.transactions:
            self._validate_transactions(block.transactions)
            
        block_id = self.block_service.store(block)
        if block_id is None:
            raise ValidateError("Invalid block")
        return block_id

    def append_chain(self, blocks: list[Block]):
        stored = []
        iterator = self.iterate_blocks()
        while len(stored) < len(blocks):
            try:
                stored.append(next(iterator))
            except StopIteration:
                break
        stored = [bl.hash for bl in stored]
        for block in blocks:
            if block.hash in stored:
                continue
            print("ADD NEW", block.hash)
            self.store_block(block)

    def generate_key(self, password: str):
        key = self.key_service.generate(password)
        key.token = str(uuid4())
        self._token_to_key[key.token] = key
        return key

    def load_key(self, address: str, password: str) -> Key | None:
        key = self.key_service.load(address, password)
        if key is None:
            raise ValidateError("Invalid address or password")
        key.token = str(uuid4())
        self._token_to_key[key.token] = key
        return key

    def load_key_by_token(self, token: str) -> Key | None:
        return self._token_to_key.get(token, None)

