from app.backend.database.block import BlockService
from app.backend.database.database import DatabaseService
from app.backend.database.transaction import TransactionService
from app.backend.database.repository import DatabaseRepository

from app.backend.engine.actor import ActorRepository, MoveDirections
from app.backend.engine.static import StaticObjectRepository
from app.backend.engine.world import WorldService

from app.backend.network.repository import NetworkRepository
from app.backend.network.request import RequestWorker
from app.backend.network.response import ResponseWorker
from app.backend.network.node import NodeService
from app.backend.network.store import NodesStore

from app.backend.repository import BackendRepository

from app.ui.repository import UIRepository
from app.ui.backend_service import BackendService

import os
import threading
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


BIND_ADDRESS = os.getenv('BIND_ADDRESS', '127.0.0.1:8989').split(':')
BIND_ADDRESS = (BIND_ADDRESS[0], int(BIND_ADDRESS[1]))
SEEDER_ADDRESS = os.getenv('SEEDER_ADDRESS', '127.0.0.1:8989').split(':')
SEEDER_ADDRESS = (SEEDER_ADDRESS[0], int(SEEDER_ADDRESS[1]))
LOCAL_MODE = int(os.getenv('LOCAL_MODE', '0'))
NODE_ONLY = int(os.getenv('NODE_ONLY', '0'))
KEY_FILENAME = os.getenv('KEY_FILENAME', 'key')

try:
    with open(KEY_FILENAME, 'rb') as f:
        private_key = Ed25519PrivateKey.from_private_bytes(f.read())
except FileNotFoundError:
    private_key = Ed25519PrivateKey.generate()
    with open(KEY_FILENAME, 'wb') as f:
        f.write(private_key.private_bytes_raw())

db_service = DatabaseService()

trans_rep = TransactionService(db_service, private_key)
block_rep = BlockService(db_service)
db_rep = DatabaseRepository(block_rep, trans_rep)

actor_rep = ActorRepository(db_rep)
static_rep = StaticObjectRepository(actor_rep, db_rep)
world_service = WorldService(world_size=50)

if not LOCAL_MODE:
    response_worker = ResponseWorker()
    nodes_store = NodesStore()
    request_worker = RequestWorker(db_rep, nodes_store)
    node_service = NodeService(BIND_ADDRESS, nodes_store, request_worker, response_worker)
    net_rep = NetworkRepository(node_service)
else:
    class NetRep:
        def __getattr__(self, *args, **kwargs):
            return self
        def __call__(self, *args, **kwargs):
            return []
    net_rep = NetRep()

backend_rep = BackendRepository(db_service, block_rep, actor_rep, net_rep, trans_rep, static_rep, db_rep, world_service)

backend_service = BackendService(backend_rep)
ui_rep = UIRepository(backend_service)


if __name__ == '__main__':
    threading.Thread(target=backend_rep.cmd_handler_thread).start()

    backend_rep.init(SEEDER_ADDRESS)
    if not NODE_ONLY:
        ui_rep.init()
        ui_rep.run()

