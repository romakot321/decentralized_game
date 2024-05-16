from app.backend.database.block import BlockRepository
from app.backend.database.database import DatabaseService
from app.backend.database.transaction import TransactionRepository
from app.backend.engine.actor import ActorRepository, MoveDirections
from app.backend.engine.static import StaticObjectRepository
from app.backend.utils import asdict
from app.backend.network.repository import NetworkRepository
from app.backend.network.socket_service import SocketService
from app.backend.network.request_factory import RequestFactory
from app.backend.network.response_factory import ResponseFactory
from app.backend.database.repository import DatabaseRepository
from app.backend.repository import BackendRepository

import os
import threading

BIND_ADDRESS = os.getenv('BIND_ADDRESS', '127.0.0.1:8989').split(':')
BIND_ADDRESS = (BIND_ADDRESS[0], int(BIND_ADDRESS[1]))


db_service = DatabaseService()
trans_rep = TransactionRepository(db_service)
block_rep = BlockRepository(db_service, trans_rep)
db_rep = DatabaseRepository(block_rep, trans_rep)

request_factory = RequestFactory()
response_factory = ResponseFactory(db_rep)
socket_service = SocketService(BIND_ADDRESS, response_factory, request_factory)
net_rep = NetworkRepository(socket_service, request_factory, response_factory)

net_rep.request_get_address_book()

