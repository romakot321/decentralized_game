from app.backend.database.models import Transaction
from app.backend.database.models import UTXOs
from app.backend.database.models import TXInput, TXOutput
from app.backend.database.models import ValidateError
from app.backend.database.models import Key

from app.backend.database.script import ScriptService, Operation
from app.backend.database.key import KeyService

from enum import Enum
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from hashlib import sha256


def hash_string(string: str) -> bytes:
    return sha256(string).digest()


class TransactionService:
    """Implements transaction pool and validator"""

    def __init__(self, db_service):
        self.db_service = db_service

    def get_utxos(
            self,
            transaction_id: str = None,
            output_index: int = None,
            output_lock_script_part: bytes = None,
            output_value: bytes = None
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
        if output_value is not None:
            utxos_list = filter(
                lambda i: any(output_value == out.value for out in i.transaction.outputs),
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
            utxos_list = self.get_utxos(transaction_id=inp.tx_id)
            if not utxos:
                continue
            for utxos in utxos_list:
                if inp.output_index not in utxos.outputs_indexes:
                    print("!@#!@#!@#$")
                    continue
                utxos.outputs_indexes.remove(inp.output_index)
                if not utxos.outputs_indexes:
                    self.db_service.delete('utxos', utxos.id)
                else:
                    self.db_service.update(utxos.id, utxos)
        return utxos

    def delete_utxos(self, tx: Transaction):
        """Delete utxos"""
        utxos_list = self.get_utxos(tx.id)
        if utxos_list:
            for utxos in utxos_list:
                self.db_service.delete('utxos', utxos.id)
        for inp in tx.inputs:
            input_tx_block = self.db_service.find('block', subfilters={'transactions': {'id': inp.tx_id}})
            if not input_tx_block:
                continue
            input_tx = [tx for tx in input_tx_block[0].transactions if tx.id == inp.tx_id][0]
            utxos = UTXOs(
                transaction_id=input_tx.id,
                outputs_indexes=[inp.output_index],
                transaction=input_tx
            )
            self.db_service.save(utxos)

    def make(
            self,
            inputs: list[TXInput],
            outputs: list[TXOutput]
    ) -> Transaction:
        inputs = [(TXInput(**inp) if isinstance(inp, dict) else inp) for inp in inputs]
        outputs = [(TXOutput(**out) if isinstance(out, dict) else out) for out in outputs]
        return Transaction(inputs=inputs, outputs=outputs)

    def make_input(
            self,
            tx_id,
            output_index,
            unlock_script: bytes = None,
            key: Key = None
    ) -> TXInput:
        """By default unlock script is tx signature + public key"""
        if unlock_script is None:
            utxos = self.get_utxos(transaction_id=tx_id)
            if not utxos:
                raise ValueError("No available utxos found for new input")
            utxos = utxos[0]
            signature = key.private_key.sign(utxos.transaction.encode())
            raw_public_key = key.public_key.public_bytes_raw()
            unlock_script = Operation.push.value + len(signature).to_bytes(8) + signature
            unlock_script += Operation.push.value + len(raw_public_key).to_bytes(8) + raw_public_key
        return TXInput(
            tx_id=tx_id,
            output_index=output_index,
            unlock_script=unlock_script
        )

    def make_output(
            self,
            input_index,
            value: bytes,
            lock_script: bytes = None,
            receiver_address: bytes = None
    ) -> TXOutput:
        """By default lock script is address of receiver"""
        if lock_script is None:
            lock_script = Operation.duplicate_top.value
            lock_script += Operation.hash_top.value
            lock_script += Operation.push.value + len(receiver_address).to_bytes(8) + receiver_address
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
            utxos = self.get_utxos(depends_tx_id)
            if not utxos:
                print("No available utxos found", depends_tx_id)
                return False
            utxos = utxos[0]
            depends[depends_tx_id] = utxos.transaction
        results = ScriptService.run_transaction(tx, depends)
        return all(results)

    def delete(self, transaction):
        if self.db_service.delete('transaction', transaction.id) is not None:
            self.delete_utxos(transaction)

    def store(self, transaction: Transaction):
        if not self.validate(transaction):
            raise ValidateError("Invalid transaction")
        self.db_service.save(transaction)

    def pop_all(self) -> list[Transaction]:
        """Clear pool and return cleared transactions"""
        txs = self.db_service.find('transaction')
        for tx in txs:
            self.delete_utxos(tx)
            self.db_service.delete('transaction', tx.id)
        return txs

