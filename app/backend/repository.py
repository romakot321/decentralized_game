import os
import threading
import time
from enum import Enum

from app.backend.engine.models import Actor
from app.backend.engine.models import Biome
from app.backend.database.models import Block
from app.backend.database.models import ValidateError
from app.backend.network.models import NetworkBlock, NetworkTransaction
from app.backend.utils import asdict


class ActorEvent(Enum):
    MOVE_UP = (0, -1)
    MOVE_RIGHT = (1, 0)
    MOVE_LEFT = (-1, 0)
    MOVE_DOWN = (0, 1)
    PICK = 0
    DROP = 1


class BackendRepository:
    """Repository with game logic"""

    def __init__(self, db_service,
                 actor_repository, network_repository,
                 static_object_repository,
                 database_repository, world_service):
        self.db_service = db_service
        self.actor_rep = actor_repository
        self.net_rep = network_repository
        self.static_rep = static_object_repository
        self.db_rep = database_repository
        self.world_service = world_service

        self.myactor = None

    def make_actor(self, password: str, address: str = None) -> Actor:
        """
        Password for private key
        If address not specified, then new key will create
        """
        return self.actor_rep.make(password, address)

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

    def get_chunk_info(self, chunk_x, chunk_y) -> Biome:
        chunk = self.world_service.get_chunk_biome(chunk_x, chunk_y)
        while chunk is None:
            self.world_service.generate_new()
            chunk = self.world_service.get_chunk_biome(chunk_x, chunk_y)
        return chunk

    def init(self, seeder_address: tuple):
        self.net_rep.init()
        self.net_rep.update_nodes_store(seeder_address)
        blocks = self.net_rep.request_blocks()
        if any(blocks):
            blocks = max(blocks, key=len)
            for i in range(len(blocks) - 1, -1, -1):
                blocks[i] = Block.from_network_model(blocks[i])
            genesis_block = blocks[-1]
            assert genesis_block.previous_hash == ''
            self.db_rep.append_chain(blocks[::-1])
            self.static_rep.init(genesis_block.hash)
        else:
            while len(blocks := list(self.db_rep.iterate_blocks())) == 0:
                pass
                block = self.db_rep.generate_block()
                print(block)
                print("GENERATED", len(block.transactions), 'transactrions')
                self.db_rep.store_block(block)
                block = NetworkBlock.from_db_model(block)
                self.net_rep.relay_block(block)
            genesis_block = next(self.db_rep.iterate_blocks())
        
        print("GENESIS", genesis_block)
        self.world_service.init(int(genesis_block.hash, 16))

    def handle_event(self, event: ActorEvent, actor_token: str, **kwargs):
        actor_key = self.db_rep.load_key_by_token(actor_token)
        if actor_key is None:
            raise ValidateError("Invalid actor token")
        tx = None

        if event in (ActorEvent.MOVE_UP, ActorEvent.MOVE_DOWN, ActorEvent.MOVE_RIGHT, ActorEvent.MOVE_LEFT):
            tx = self.actor_rep.make_move(actor_key, event)
        elif event == ActorEvent.PICK:
            tx = self.static_rep.pick_object(actor_key)
        elif event == ActorEvent.DROP:
            tx = self.static_rep.drop_object(actor_key=actor_key, object_id=kwargs['object_id'])

        if not tx:
            return
        self.db_rep.store_transaction(tx)
        net_tx = NetworkTransaction.from_db_model(tx)
        self.net_rep.relay_transaction(net_tx)
        return tx

    def cmd_handler_thread(self):
        while True:
            cmd = input("Enter command: ").lower()
            if cmd == 'blocks':
                for block in self.db_rep.iterate_blocks():
                    print(str(block))
            elif cmd == 'objects':
                object_txs = self.static_rep.init(next(self.db_rep.iterate_blocks()).hash)
                for tx in object_txs:
                    self.db_rep.store_transaction(tx)
                block = self.db_rep.generate_block()
                self.db_rep.store_block(block)
            elif cmd == 'gen':
                block = self.db_rep.generate_block()
                print(block)
                print("GENERATED", len(block.transactions), 'transactrions')
                self.db_rep.store_block(block)
                block = NetworkBlock.from_db_model(block)
                self.net_rep.relay_block(block)
            elif cmd == 'inv':
                print(self.static_rep.get_actor_picked(self.myactor.id))
            elif cmd == 'txs':
                print(*map(str, self.db_rep.find_utxos()), sep='\n')
            elif cmd == 'abc':
                self.db_rep.tx_service.db_service.abc()
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

