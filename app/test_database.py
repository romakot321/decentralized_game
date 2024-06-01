from app.backend.database.block import BlockService
from app.backend.database.database import DatabaseService
from app.backend.database.transaction import TransactionService
from app.backend.database.repository import DatabaseRepository

from app.backend.engine.actor import ActorRepository
from app.backend.engine.actor import MoveDirections

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


private_key = Ed25519PrivateKey.generate()

db_service = DatabaseService()

tx_service = TransactionService(db_service, private_key)
block_rep = BlockService(db_service)
db_rep = DatabaseRepository(block_rep, tx_service)
actor_rep = ActorRepository(database_repository=db_rep)


if __name__ == '__main__':
    actor = actor_rep.make()
    tx = actor_rep.move(actor.id, MoveDirections.RIGHT)
    tx = actor_rep.move(actor.id, MoveDirections.RIGHT)
    tx = actor_rep.move(actor.id, MoveDirections.RIGHT)
    block = db_rep.generate_block()
    db_rep.store_block(block, validate_transactions=False)
    print(actor_rep.get_position(actor.id))


