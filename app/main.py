from app.backend.database.block import BlockService
from app.backend.database.database import DatabaseService
from app.backend.database.transaction import TransactionService
from app.backend.engine.actor import ActorRepository, MoveDirections
from app.backend.engine.static import StaticObjectRepository
from app.backend.network.repository import NetworkRepository
from app.backend.network.socket_service import SocketService
from app.backend.network.request_factory import RequestFactory
from app.backend.network.response_factory import ResponseFactory
from app.backend.repository import BackendRepository
from app.backend.database.repository import DatabaseRepository

from app.ui.repository import UIRepository
from app.ui.backend_service import BackendService

import os
import threading
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


BIND_ADDRESS = os.getenv('BIND_ADDRESS', '127.0.0.1:8989').split(':')
BIND_ADDRESS = (BIND_ADDRESS[0], int(BIND_ADDRESS[1]))
private_key = Ed25519PrivateKey.generate()

db_service = DatabaseService()

trans_rep = TransactionService(db_service, private_key)
block_rep = BlockService(db_service)
db_rep = DatabaseRepository(block_rep, trans_rep)

actor_rep = ActorRepository(db_rep)
static_rep = StaticObjectRepository(actor_rep, trans_rep, block_rep)

request_factory = RequestFactory(db_rep)
response_factory = ResponseFactory(db_rep)
socket_service = SocketService(BIND_ADDRESS, response_factory, request_factory)
net_rep = NetworkRepository(socket_service, db_rep, request_factory, response_factory)

backend_rep = BackendRepository(db_service, block_rep, actor_rep, net_rep, trans_rep, static_rep, db_rep)

backend_service = BackendService(backend_rep)
ui_rep = UIRepository(backend_service)


if __name__ == '__main__':
    #threading.Thread(target=backend_rep.cmd_handler_thread).start()

    backend_rep.init()
    ui_rep.run()

