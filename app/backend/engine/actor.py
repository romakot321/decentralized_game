from app.backend.engine.models import Actor
from app.backend.database.models import TransactionsAction
from uuid import UUID
from enum import Enum


class MoveDirections(Enum):
    UP = (0, 1)
    RIGHT = (1, 0)
    DOWN = (0, -1)
    LEFT = (-1, 0)


class ActorRepository:
    def __init__(self, block_repository, transaction_repository):
        self.block_rep = block_repository
        self.trans_rep = transaction_repository
        self._pos_cache = {}
        self._actors_cache = (None, set())

    def make(self) -> Actor:
        return Actor()

    def move(self, actor_id: UUID, direction: MoveDirections):
        transaction = self.trans_rep.make(
            actor_id,
            data=direction.value,
            action=TransactionsAction.MOVE,
        )
        self.trans_rep.store(transaction)

    def _cache_pos_calculation(self, actor_id, block_hash, pos):
        self._pos_cache[actor_id] = (block_hash, pos)

    def _get_cached_pos(self, actor_id) -> tuple[str, tuple] | None:
        return self._pos_cache.get(actor_id)

    def get_many(self) -> list[Actor]:
        actors = set()
        for block in self.block_rep.iterate_blocks(stop_hash=self._actors_cache[0]):
            for trans in block.transactions:
                actors.add(trans.actor)
        actors |= self._actors_cache[1]
        self._actors_cache = (self.block_rep.get_last().previous_hash, actors)
        return [Actor(id=i) for i in actors]

    def get_position(self, actor_id) -> tuple[int, int]:
        curr_pos = (0, 0)
        cached_data = self._get_cached_pos(actor_id)
        cached_block_hash, cached_pos = cached_data if cached_data else (None, (0, 0))

        for block in self.block_rep.iterate_blocks(stop_hash=cached_block_hash):
            for trans in block.transactions:
                if trans.action == TransactionsAction.MOVE.value and str(trans.actor) == str(actor_id):
                    bias = trans.unpack_data().bias
                    curr_pos = (curr_pos[0] + bias[0], curr_pos[1] + bias[1])

        curr_pos = (curr_pos[0] + cached_pos[0], curr_pos[1] + cached_pos[1])
        self._cache_pos_calculation(actor_id, self.block_rep.get_last().hash, curr_pos)
        return curr_pos

