import random
from uuid import uuid5, NAMESPACE_DNS, UUID

from app.backend.engine.models import StaticObject
from app.backend.engine.actor import MoveDirections
from app.backend.database.models import Transaction
from app.backend.database.script import Operation


class StaticObjectRepository:
    def __init__(self, actor_repository, database_repository):
        self.actor_rep = actor_repository
        self.db_rep = database_repository

        self.seed = None
        self.world = []

    def make_object_unlock_script(self, position: tuple[int, int]) -> bytes:
        position_encoded = ';'.join(map(str, position)).encode()
        script = Operation.push.value + len(position_encoded).to_bytes() + position_encoded
        script += Operation.push_alt.value
        script += Operation.check_equal.value
        return script

    def make_object_transaction(self, obj: StaticObject) -> Transaction:
        outputs = [
            self.db_rep.make_transaction_output(
                input_index=-1,
                value=obj.object_id.encode(),
                lock_script=self.make_object_unlock_script(obj.position)
            )
        ]
        tx = self.db_rep.make_transaction(inputs=[], outputs=outputs)
        return tx

    def find_object_transaction(self, object_id: str) -> Transaction | None:
        for utxos in self.db_rep.find_utxos(output_value=object_id.encode()):
            return utxos.transaction

    def make_pick_transaction(self, object_id: str, actor_id: str):
        object_tx = self.find_object_transaction(object_id)
        actor_move_tx, actor_move_tx_out = self.actor_rep.get_actor_outputs(actor_id, movement=True)[0]
        inputs = [
            self.db_rep.make_transaction_input(
                tx_id=object_tx.id,
                output_index=0,
                unlock_script=b''
            ),
            self.db_rep.make_transaction_input(
                tx_id=actor_move_tx.id,
                output_index=actor_move_tx.outputs.index(actor_move_tx_out)
            )
        ]
        outputs = [
            self.db_rep.make_transaction_output(
                input_index=0,
                value=object_tx.outputs[0].value
            ),
            self.db_rep.make_transaction_output(
                input_index=1,
                value=actor_move_tx_out.value
            )
        ]
        return self.db_rep.make_transaction(inputs=inputs, outputs=outputs)

    def init(self) -> list[Transaction]:
        """Return list of transactions to save"""
        genesis_block = self.db_rep.block_service.get_many(previous_hash='')
        if genesis_block:
            self.seed = genesis_block[0].hash
            random.seed(self.seed)
        
        txs = []
        for _ in range(random.randint(3, 7)):
            pos = (random.randint(0, 10), random.randint(0, 10))
            self.world.append(
                StaticObject(
                    position=pos,
                    object_id=str(uuid5(NAMESPACE_DNS, str(random.randbytes(10))))
                )
            )
            txs.append(self.make_object_transaction(self.world[-1]))
        return txs

    def get_many(self):
        self.check_remove()
        return self.world

    def get_actor_picked(self, actor_id) -> list[str]:
        picked = []
        for utxos in self.db_rep.find_utxos(output_lock_script_part=actor_id):
            for out_index in utxos.outputs_indexes:
                out = utxos.transaction.outputs[out_index]
                try:
                    UUID(out.value.decode())
                except ValueError:
                    continue
                picked.append(out.value.decode())
        return picked

    def delete(self, object_id):
        for i in range(len(self.world)):
            if self.world[i].object_id == object_id:
                self.world.pop(i)
                return

    def check_remove(self):
        for utxos in self.db_rep.find_utxos():
            for out in utxos.transaction.outputs:
                if out.value in [o.object_id.encode() for o in self.world] \
                        and len(utxos.transaction.outputs) != 1:
                    self.delete(out.value.decode())
                    break

    def pick_object(self, actor_id: str) -> Transaction | None:
        actor_pos = self.actor_rep.get_position(actor_id)
        tx = None
        for obj in self.world:
            if actor_pos == obj.position:
                tx = self.make_pick_transaction(obj.object_id, actor_id)
                break
        self.check_remove()
        return tx

