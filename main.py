from backend.database.block import BlockRepository
from backend.database.database import DatabaseService
from backend.database.transaction import TransactionRepository
from backend.engine.actor import ActorRepository, MoveDirections
from backend.engine.static import StaticObjectRepository
from backend.utils import asdict
from backend.network.network import NetworkHandler
from backend.repository import BackendRepository

from ui.repository import UIRepository

import os
import threading


BIND_ADDRESS = os.getenv('BIND_ADDRESS', '127.0.0.1:8989').split(':')
BIND_ADDRESS = (BIND_ADDRESS[0], int(BIND_ADDRESS[1]))


db_service = DatabaseService()
trans_rep = TransactionRepository(db_service)
block_rep = BlockRepository(db_service, trans_rep)
actor_rep = ActorRepository(block_rep, trans_rep)
static_rep = StaticObjectRepository(actor_rep, trans_rep, block_rep)
nh = NetworkHandler(BIND_ADDRESS, block_rep)
backend_rep = BackendRepository(db_service, block_rep, actor_rep, nh, trans_rep, static_rep)

ui_rep = UIRepository(backend_rep)


if __name__ == '__main__':
    threading.Thread(target=backend_rep.cmd_handler_thread).start()

    backend_rep.init()
    ui_rep.run()

