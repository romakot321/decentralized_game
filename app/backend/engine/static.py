import random
from uuid import uuid5, NAMESPACE_X500

from app.backend.engine.models import StaticObject
from app.backend.database.models import TransactionsAction
from app.backend.database.models import PickTransaction


class StaticObjectRepository:
    def __init__(self, actor_repository, transaction_repository, block_repository):
        self.actor_rep = actor_repository
        self.trans_rep = transaction_repository
        self.block_rep = block_repository

        self.seed = None
        self.world = []

    def init(self):
        genesis_block = self.block_rep.get_many(previous_hash='')
        if genesis_block:
            self.seed = genesis_block[0].hash
            random.seed(self.seed)

        for _ in range(random.randint(1, 5)):
            pos = (random.randint(2, 7), random.randint(2, 7))
            self.world.append(
                StaticObject(
                    position=pos,
                    object_id=str(uuid5(NAMESPACE_X500, random.randbytes(10)))
                )
            )

    def get_many(self):
        self.check_remove()
        return self.world

    def get_actor_picked(self, actor_id) -> list:
        objects = set()
        for block in self.block_rep.iterate_blocks():
            for transaction in block.transactions:
                if transaction.action != TransactionsAction.PICK.value:
                    continue
                if transaction.actor != actor_id:
                    continue
                data = transaction.unpack_data()
                objects.add(data.object_id)
        return list(objects)

    def delete(self, object_id):
        for i in range(len(self.world)):
            if self.world[i].object_id == object_id:
                self.world.pop(i)
                return

    def check_remove(self):
        for block in self.block_rep.iterate_blocks():
            for transaction in block.transactions:
                if transaction.action != TransactionsAction.PICK.value:
                    continue
                data = transaction.unpack_data()
                if data.object_id in [i.object_id for i in self.world]:
                    self.delete(data.object_id)

    def check_collisions(self):
        for actor in self.actor_rep.get_many():
            pos = self.actor_rep.get_position(actor.id)
            for obj in self.world:
                if pos == obj.position:
                    trans = self.trans_rep.make(
                        actor=actor.id,
                        data=PickTransaction.TransactionData(
                            pick_position=pos,
                            object_id=obj.object_id
                        ),
                        action=TransactionsAction.PICK
                    )
                    self.trans_rep.store(trans)
        self.check_remove()
