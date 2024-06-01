from app.backend.engine.models import Actor
from app.backend.database.models import Transaction
from uuid import UUID
from enum import Enum


class MoveDirections(Enum):
    UP = (0, 1)
    RIGHT = (1, 0)
    DOWN = (0, -1)
    LEFT = (-1, 0)


class ActorRepository:
    def __init__(self, database_repository):
        self.db_rep = database_repository
        self.actor_id = self.db_rep.tx_service.address
        self._pos_cache = {}
        self._actors_cache = (None, set())

    def make(self) -> Actor:
        return Actor(id=self.actor_id)

    def get_actor_unspent_transactions(self, actor_id: str) -> list:
        txs = []
        utxos_list = self.db_rep.find_utxos(output_lock_script_part=actor_id)
        for utxos in utxos_list:
            for out_index in utxos.outputs_indexes:
                if actor_id in utxos.transaction.outputs[out_index].lock_script:
                    txs.append(utxos.transaction)
        return txs

    def get_actor_outputs(self, actor_id, movement: bool = False) -> list[tuple]:
        """Return list of (Transaction, output)"""
        outputs = []
        txs = self.get_actor_unspent_transactions(actor_id)
        for tx in txs:
            for out in tx.outputs:
                if movement and b';' in out.value:
                    outputs.append((tx, out))
        return outputs

    def move(self, actor_id: str, direction: MoveDirections) -> Transaction:
        tx_inputs = []

        curr_pos = self.get_position(actor_id)
        new_pos = (curr_pos[0] + direction.value[0], curr_pos[1] + direction.value[1])
        move_output = self.get_actor_outputs(actor_id, movement=True)
        
        if move_output:
            move_output = move_output[0]
            tx_inputs.append(self.db_rep.make_transaction_input(
                tx_id=move_output[0].id,
                output_index=move_output[0].outputs.index(move_output[1])
            ))
        tx_outputs = [
            self.db_rep.make_transaction_output(
                input_index=0,
                value=';'.join(map(str, new_pos)).encode()
            )
        ]
        tx = self.db_rep.make_transaction(tx_inputs, tx_outputs)
        self.db_rep.store_transaction(tx)
        return tx

    def _cache_pos_calculation(self, actor_id, block_hash, pos):
        self._pos_cache[actor_id] = (block_hash, pos)

    def _get_cached_pos(self, actor_id) -> tuple[str, tuple] | None:
        return self._pos_cache.get(actor_id)

    def get_many(self) -> list[Actor]:
        return [Actor(id=self.actor_id)]
        actors = set()
        for block in self.block_rep.iterate_blocks(stop_hash=self._actors_cache[0]):
            for trans in block.transactions:
                actors.add(trans.actor)
        actors |= self._actors_cache[1]
        self._actors_cache = (self.block_rep.get_last().previous_hash, actors)
        return [Actor(id=i) for i in actors]

    def get_position(self, actor_id) -> tuple[int, int]:
        move_outputs = self.get_actor_outputs(actor_id, movement=True)
        if move_outputs:
            x, y = move_outputs[0][1].value.decode().split(';')
            return int(x), int(y)
        return 0, 0

