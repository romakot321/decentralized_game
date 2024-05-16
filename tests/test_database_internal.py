from app.backend.database.models import MoveTransaction
from app.backend.database.models import PickTransaction
from app.backend.database.models import Block
from app.backend.engine.models import Actor, StaticObject
import random
import struct
from hashlib import sha256

test_actor = Actor()
move_trans_data = MoveTransaction.pack_data((132131230, 200000))
move_trans = MoveTransaction(
    data=move_trans_data,
    actor=test_actor.id
)
pick_trans_data = PickTransaction.pack_data(((12, 10), 1))
pick_trans = PickTransaction(
    data=pick_trans_data,
    actor=test_actor.id
)

block = Block(
    transactions=[move_trans, pick_trans],
    previous_hash=sha256(b'a').hexdigest()
)


def test_move_transaction():
    move_trans_dumped = move_trans.dump()
    undumped_trans = MoveTransaction.undump(move_trans_dumped)
    assert undumped_trans.data == move_trans.data


def test_pick_transaction():
    pick_trans_dumped = pick_trans.dump()
    undumped_trans = PickTransaction.undump(pick_trans_dumped)
    assert pick_trans.data == undumped_trans.data


def test_block():
    dumped_block = block.dump()
    print(len(dumped_block))
    undumped_block = Block.undump(dumped_block)
    print(undumped_block)


test_move_transaction()
test_pick_transaction()
test_block()
