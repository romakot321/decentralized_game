from block import BlockRepository
from database import DatabaseService
from actor import ActorRepository, MoveDirections
from utils import asdict
from network import NetworkHandler
import os
import threading
import time

db_service = DatabaseService()
block_rep = BlockRepository(db_service)
actor_rep = ActorRepository(block_rep)

BIND_ADDRESS = os.getenv('BIND_ADDRESS', '127.0.0.1:8989').split(':')
BIND_ADDRESS = (BIND_ADDRESS[0], int(BIND_ADDRESS[1]))
nh = NetworkHandler(BIND_ADDRESS, block_rep)
nh.update_address_book()

genesis_block = block_rep.make([])
block_rep.store(genesis_block)
nh.update_address_book()

myactor = actor_rep.create()

nh.update_blocks()

for block in block_rep.iterate_blocks():
    if block.previous_hash == '':
        print("World seed =", block.hash)

new_block = block_rep.make([
    actor_rep.make_move(myactor.id, MoveDirections.RIGHT),
    actor_rep.make_move(myactor.id, MoveDirections.UP),
])
block_rep.store(new_block)
nh.translate_new_block(new_block)

actors = set()
actors_positions = {}
print("Your actor id:", myactor.id)
flag = False


def cmd_handler_thread():
    global flag
    while True:
        cmd = input().lower()
        if cmd == 'blocks':
            for block in block_rep.iterate_blocks():
                print(str(block))
            flag = True
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
                transaction = actor_rep.make_move(myactor.id, direction)
                block = block_rep.make([transaction])
                block_rep.store(block)
                nh.translate_new_block(block)


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

