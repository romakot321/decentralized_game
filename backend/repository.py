from backend.block import BlockRepository
from backend.database import DatabaseService
from backend.actor import ActorRepository, MoveDirections
from backend.utils import asdict
from backend.network import NetworkHandler
import os
import threading
import time


class BackendRepository:
    def __init__(self, db_service, block_repository,
                 actor_repository, network_handler):
        self.db_service = db_service
        self.block_rep = block_repository
        self.actor_rep = actor_repository
        self.net_handler = network_handler

        self.myactor = None

    def get_actors_positions(self) -> dict[tuple[int, int], str]:
        actors_position = {}
        actors = set()
        for block in self.block_rep.iterate_blocks():
            for trans in block.transactions:
                actors.add(trans.actor)
        for actor in actors:
            actors_position[self.actor_rep.get_position(actor)] = actor
        return actors_position

    def init(self):
        genesis_block = self.block_rep.make([])
        self.block_rep.store(genesis_block)

        self.net_handler.update_address_book()
        self.net_handler.update_blocks()

        self.myactor = self.actor_rep.create()
        new_block = self.block_rep.make([
            self.actor_rep.make_move(self.myactor.id, MoveDirections.RIGHT),
            self.actor_rep.make_move(self.myactor.id, MoveDirections.UP),
        ])
        self.block_rep.store(new_block)
        self.net_handler.translate_new_block(new_block)

    def cmd_handler_thread(self):
        while True:
            cmd = input("Enter command: ").lower()
            if cmd == 'blocks':
                for block in self.block_rep.iterate_blocks():
                    print(str(block))
            if cmd:
                direction = None
                if cmd == 'd':
                    direction = MoveDirections.RIGHT
                elif cmd == 'a':
                    direction = MoveDirections.LEFT
                elif cmd == 's':
                    direction = MoveDirections.UP
                elif cmd == 'w':
                    direction = MoveDirections.DOWN
                if direction:
                    transaction = self.actor_rep.make_move(self.myactor.id, direction)
                    block = self.block_rep.make([transaction])
                    self.block_rep.store(block)
                    self.net_handler.translate_new_block(block)


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

