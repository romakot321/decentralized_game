from app.backend.database.models import Transaction
from app.backend.database.models import UTXOs
from app.backend.database.models import TXInput, TXOutput
from app.backend.database.models import ValidateError

from app.backend.database.script import ScriptService, Operation

from enum import Enum
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from hashlib import sha256


def hash_string(string: str) -> bytes:
    return sha256(string).digest()


class TransactionService:
    """Implements transaction pool and validator"""

    def __init__(self, db_service, private_key: Ed25519PrivateKey | bytes):
        if isinstance(private_key, bytes):
            private_key = Ed25519PrivateKey.from_private_bytes(private_key)

        self.db_service = db_service
        self.private_key = private_key
        self.public_key = self.private_key.public_key()
        self.address = hash_string(self.public_key.public_bytes_raw())

    def get_utxos(
            self,
            transaction_id: str = None,
            output_index: int = None,
            output_lock_script_part: bytes = None
    ) -> list[UTXOs]:
        """
        :param output_lock_script_part: Check if part in output.lock_script
        """
        filters = {'transaction_id': transaction_id} if transaction_id is not None else {}
        utxos_list = self.db_service.find('utxos', **filters)
        if output_index is not None:
            utxos_list = filter(lambda i: output_index in i.outputs_indexes, utxos_list)
        if output_lock_script_part is not None:
            utxos_list = filter(
                lambda i: any(output_lock_script_part in out.lock_script for out in i.transaction.outputs),
                utxos_list
            )
        return list(utxos_list)

    def create_utxos(self, tx: Transaction):
        """Create and save new utxos and remove input utxos"""
        utxos = UTXOs(
            transaction_id=tx.id,
            outputs_indexes=[i for i in range(len(tx.outputs))],
            transaction=tx
        )
        self.db_service.save(utxos)
        for inp in tx.inputs:
            utxos = self.get_utxos(transaction_id=inp.tx_id)
            if not utxos:
                continue
            utxos = utxos[0]
            utxos.outputs_indexes.remove(inp.output_index)
            if not utxos.outputs_indexes:
                self.db_service.delete('utxos', utxos.id)
            else:
                self.db_service.update(utxos.id, utxos)
        return utxos

    def make(
            self,
            inputs: list[TXInput],
            outputs: list[TXOutput]
    ) -> Transaction:
        return Transaction(inputs=inputs, outputs=outputs)

    def make_input(self, tx_id, output_index, unlock_script: bytes = None) -> TXInput:
        """By default unlock script is tx signature + public key"""
        if unlock_script is None:
            utxos = self.get_utxos(transaction_id=tx_id)
            if not utxos:
                raise ValueError("No available utxos found for new input")
            utxos = utxos[0]
            signature = self.private_key.sign(utxos.transaction.encode())
            raw_public_key = self.public_key.public_bytes_raw()
            unlock_script = Operation.push.value + len(signature).to_bytes() + signature
            unlock_script += Operation.push.value + len(raw_public_key).to_bytes() + raw_public_key
        return TXInput(
            tx_id=tx_id,
            output_index=output_index,
            unlock_script=unlock_script
        )

    def make_output(self, input_index, value: bytes, lock_script: bytes = None) -> TXOutput:
        """By default lock script is address of receiver"""
        if lock_script is None:
            lock_script = Operation.duplicate_top.value
            lock_script += Operation.hash_top.value
            lock_script += Operation.push.value + len(self.address).to_bytes() + self.address
            lock_script += Operation.check_equal.value
            lock_script += Operation.verify_signature.value
        return TXOutput(
            input_index=input_index,
            value=value,
            lock_script=lock_script
        )

    def validate(self, tx: Transaction) -> bool:
        depends = {}
        for depends_tx_id in ScriptService.get_transaction_depends(tx):
            utxos = self.get_utxos(depends_tx_id)[0]
            depends[depends_tx_id] = utxos.transaction
        results = ScriptService.run_transaction(tx, depends)
        return all(results)

    def store(self, transaction: Transaction):
        if not self.validate(transaction):
            raise ValidateError("Invalid transaction")
        self.db_service.save(transaction)

    def pop_all(self) -> list[Transaction]:
        """Clear pool and return cleared transactions"""
        txs = self.db_service.find('transaction')
        for tx in txs:
            self.db_service.delete('transaction', tx.id)
        return txs

