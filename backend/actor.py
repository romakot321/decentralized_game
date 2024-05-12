from backend.models import Actor
from backend.models import MoveTransaction, MoveTransactionData
from uuid import UUID
from enum import Enum


class MoveDirections(Enum):
    UP = (0, 1)
    RIGHT = (1, 0)
    DOWN = (0, -1)
    LEFT = (-1, 0)


class ActorRepository:
    def __init__(self, block_repository):
        self.block_rep = block_repository
        self.cache = {}

    def create(self) -> Actor:
        actor = Actor()
        return actor

    def make_move(self, actor_id: UUID, direction: MoveDirections) -> MoveTransaction:
        move = MoveTransactionData(bias=direction.value)
        transaction = MoveTransaction(
            data=MoveTransaction.pack_data(move),
            actor=actor_id
        )
        return transaction

    def _cache_pos_calculation(self, actor_id, block_hash, pos):
        self.cache[actor_id] = (block_hash, pos)

    def _get_cached_pos(self, actor_id) -> tuple[str, tuple] | None:
        return self.cache.get(actor_id)

    def get_position(self, actor_id) -> tuple[int, int]:
        curr_pos = (0, 0)
        cached_data = self._get_cached_pos(actor_id)
        cached_block_hash, cached_pos = cached_data if cached_data else (None, (0, 0))

        for block in self.block_rep.iterate_blocks(stop_hash=cached_block_hash):
            for trans in block.transactions:
                if trans.action == 'move' and str(trans.actor) == str(actor_id):
                    bias = trans.unpack_data().bias
                    curr_pos = (curr_pos[0] + bias[0], curr_pos[1] + bias[1])

        curr_pos = (curr_pos[0] + cached_pos[0], curr_pos[1] + cached_pos[1])
        self._cache_pos_calculation(actor_id, self.block_rep.get_last().previous_hash, curr_pos)
        return curr_pos

