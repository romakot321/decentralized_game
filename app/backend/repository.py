import os
import threading
import time
from enum import Enum

from app.backend.engine.models import Actor


class ActorEvent(Enum):
    MOVE_UP = (0, -1)
    MOVE_RIGHT = (1, 0)
    MOVE_LEFT = (-1, 0)
    MOVE_DOWN = (0, 1)
    PICK = 0
    DROP = 1


class BackendRepository:
    def __init__(self, db_service, block_repository,
                 actor_repository, network_repository,
                 transaction_repository, static_object_repository,
                 database_repository):
        self.db_service = db_service
        self.block_rep = block_repository
        self.actor_rep = actor_repository
        self.net_rep = network_repository
        self.trans_rep = transaction_repository
        self.static_rep = static_object_repository
        self.db_rep = database_repository

        self.myactor = None

    def make_actor(self) -> Actor:
        return self.actor_rep.make()

    def get_actors_positions(self) -> dict[tuple[int, int], str]:
        actors_position = {}
        actors = self.actor_rep.get_many()
        for actor in actors:
            actors_position[self.actor_rep.get_position(actor.id)] = actor
        return actors_position

    def get_actor_position(self, actor_id: str) -> tuple[int, int]:
        return self.actor_rep.get_position(actor_id)

    def get_static_objects_positions(self) -> list[tuple]:
        return self.static_rep.get_many()

    def get_actor_picked(self, actor_id) -> list[str]:
        return self.static_rep.get_actor_picked(actor_id)

    def init(self):
        genesis_block = self.db_rep.make_block(transactions=[])
        self.block_rep.store(genesis_block)

        self.net_rep.init()
        self.net_rep.request_get_address_book()
        blocks = self.net_rep.request_get_blocks()
        if blocks:
            self.block_rep.replace_chain(blocks)

        #self.myactor = self.actor_rep.make()
        #new_block = self.db_rep.make_block([
        #    self.trans_rep.make(self.myactor.id, ActorEvent.MOVE_RIGHT.value, action=TransactionsAction.MOVE),
        #    self.trans_rep.make(self.myactor.id, ActorEvent.MOVE_DOWN.value, action=TransactionsAction.MOVE),
        #])
        #self.block_rep.store(new_block)
        #self.net_rep.request_publish_block(new_block)

        object_txs = self.static_rep.init()
        for tx in object_txs:
            self.db_rep.store_transaction(tx)

    def handle_event(self, event: ActorEvent, actor_id: str, **kwargs):
        if event in (ActorEvent.MOVE_UP, ActorEvent.MOVE_DOWN, ActorEvent.MOVE_RIGHT, ActorEvent.MOVE_LEFT):
            move_tx = self.actor_rep.make_move(actor_id, event)
            self.db_rep.store_transaction(move_tx)
            block = self.db_rep.generate_block()
            self.block_rep.store(block)
            self.net_rep.request_publish_block(block)
        elif event == ActorEvent.PICK:
            pick_tx = self.static_rep.pick_object(actor_id)
            if not pick_tx:
                print("No object found")
                return
            self.db_rep.store_transaction(pick_tx)
            block = self.db_rep.generate_block()
            self.block_rep.store(block)
            self.net_rep.request_publish_block(block)
        elif event == ActorEvent.DROP:
            drop_tx = self.static_rep.drop_object(actor_id=actor_id, object_id=kwargs['object_id'])
            self.db_rep.store_transaction(drop_tx)

    def cmd_handler_thread(self):
        while True:
            cmd = input("Enter command: ").lower()
            if cmd == 'blocks':
                for block in self.block_rep.iterate_blocks():
                    print(str(block))
            elif cmd == 'inv':
                print(self.static_rep.get_actor_picked(self.myactor.id))
            event = None
            if cmd == 'd':
                event = ActorEvent.MOVE_RIGHT
            elif cmd == 'a':
                event = ActorEvent.MOVE_LEFT
            elif cmd == 's':
                event = ActorEvent.MOVE_DOWN
            elif cmd == 'w':
                event = ActorEvent.MOVE_UP
            if event:
                self.handle_event(event)
                

if __name__ == '__main__':
    actors = set()
    actors_positions = {}
    print("Your actor id:", myactor.id)
    flag = False

    threading.Thread(target=cmd_handler_thread).start()

    while True:
        for block in block_rep.iterate_blocks():
            for trans in block.transactions:
                actors.add(str(trans.actor))
        actors_positions.clear()
        for actor in actors:
            actors_positions[actor_rep.get_position(actor)] = actor

        if flag:
            time.sleep(10)
            flag = False
        os.system('cls' if os.name=='nt' else 'clear')
        for y in range(5):
            for x in range(20):
                char = '.'
                if (x, y) in actors_positions.keys():
                    if myactor.id == actors_positions[(x, y)]:
                        char = '#'
                    else:
                        char = '@'
                print(char, end='')
            print()
        if flag:
            time.sleep(10)
            flag = False
        time.sleep(0.5)

