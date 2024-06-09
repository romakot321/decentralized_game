from app.backend.engine.models import Actor
from app.backend.database.models import Transaction
from uuid import UUID
from enum import Enum


class MoveDirections(Enum):
    UP = (0, 1)
    RIGHT = (1, 0)
    DOWN = (0, -1)
    LEFT = (-1, 0)
    STAND = (0, 0)


class ActorRepository:
    def __init__(self, database_repository):
        self.db_rep = database_repository
        self.actor_id = self.db_rep.tx_service.address
        self._pos_cache = {}
        self._actors_cache = (None, set())

    def make(self) -> Actor:
        return Actor(id=self.actor_id)

    def get_actor_unspent_transactions(self, actor_id: str) -> list[tuple[Transaction, int]]:
        txs = []
        utxos_list = self.db_rep.find_utxos(output_lock_script_part=actor_id)
        for utxos in utxos_list:
            for out_index in utxos.outputs_indexes:
                if actor_id in utxos.transaction.outputs[out_index].lock_script:
                    txs.append((utxos.transaction, out_index))
        return txs

    def get_actor_outputs(
            self,
            actor_id,
            movement: bool = False,
            pick: bool = False
    ) -> list[tuple]:
        """Return list of (Transaction, output)"""
        outputs = []
        txs = self.get_actor_unspent_transactions(actor_id)
        for tx, out_index in txs:
            out = tx.outputs[out_index]
            if movement and b';' in out.value:
                outputs.append((tx, out))
            if pick and out.value.count(b'-') == 4:
                outputs.append((tx, out))
        return outputs

    def make_move(self, actor_id: str, direction: MoveDirections) -> Transaction:
        tx_inputs = []

        curr_pos = self.get_position(actor_id)
        new_pos = (curr_pos[0] + direction.value[0], curr_pos[1] + direction.value[1])
        move_outputs = self.get_actor_outputs(actor_id, movement=True)
        
        if move_outputs:
            move_tx, move_output = move_outputs[0]
            tx_inputs.append(self.db_rep.make_transaction_input(
                tx_id=move_tx.id,
                output_index=move_tx.outputs.index(move_output)
            ))
        tx_outputs = [
            self.db_rep.make_transaction_output(
                input_index=0,
                value=';'.join(map(str, new_pos)).encode()
            )
        ]
        tx = self.db_rep.make_transaction(tx_inputs, tx_outputs)
        return tx

    def _cache_pos_calculation(self, actor_id, block_hash, pos):
        self._pos_cache[actor_id] = (block_hash, pos)

    def _get_cached_pos(self, actor_id) -> tuple[str, tuple] | None:
        return self._pos_cache.get(actor_id)

    def get_many(self) -> list[Actor]:
        actors = set()
        utxos_list = self.db_rep.find_utxos()
        for utxos in utxos_list:
            for out_index in utxos.outputs_indexes:
                if b';' in utxos.transaction.outputs[out_index].value:
                    actors.add(utxos.transaction.outputs[out_index].lock_script)
        return [Actor(id=i) for i in actors]

    def get_position(self, actor_id) -> tuple[int, int]:
        move_outputs = self.get_actor_outputs(actor_id, movement=True)
        if move_outputs:
            x, y = move_outputs[0][1].value.decode().split(';')
            return int(x), int(y)
        return 0, 0

