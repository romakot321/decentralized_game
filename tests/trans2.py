from dataclasses import dataclass
from enum import Enum
import json
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from hashlib import sha256
import base64


@dataclass
class TXInput:
    tx_id: int
    output_index: int
    unlock_script: bytes


@dataclass
class TXOutput:
    input_index: int
    lock_script: bytes


@dataclass
class Transaction:
    inputs: list[TXInput]
    data: str
    outputs: list[TXOutput]
    id: int

    def encode(self):
        return sha256(f'{self.inputs}{self.data}{self.outputs}{self.id}'.encode()).digest()


chain = []


def find_utxos() -> list[Transaction]:
    ret = []
    for tx in chain[::-1]:
        used_outputs = []
        for tx2 in chain:
            for inp in tx2.inputs:
                if inp.tx_id == tx.id:
                    used_outputs.append(inp.output_index)
        if len(used_outputs) < len(tx.outputs):
            ret.append(tx)
    return ret


def validate_input(inp: TXInput):
    tx_for_validation = None
    for tx in chain:
        if tx.id == inp.tx_id:
            tx_for_validation = tx
    if not tx_for_validation:
        return
    output_for_validation = tx_for_validation.outputs[inp.output_index]
    signature, pubkey = inp.unlock_script[:64], inp.unlock_script[64:]
    if base64.b64encode(pubkey) != output_for_validation.lock_script:
        raise ValueError("Invalid public key in input")
    pubkey = Ed25519PublicKey.from_public_bytes(pubkey)
    pubkey.verify(signature, tx_for_validation.encode())


def make_tx(inputs, data, outputs) -> Transaction:
    return Transaction(
        inputs=inputs,
        data=data,
        outputs=outputs,
        id=len(chain)
    )


def find_player_last_tx(player_id) -> Transaction | None:
    for tx in find_utxos():
        if any([out.lock_script == player_id for out in tx.outputs]):
            return tx


def add_object(object_id: str, object_pos: tuple[int, int]):
    outputs = [TXOutput(input_index=0, lock_script=sha256(str(object_pos).encode()).digest())]
    tx = make_tx(inputs=[], data=object_id, outputs=outputs)
    chain.append(tx)


class PlayerService:
    def __init__(self):
        self.private_key = Ed25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()
        self.address = base64.b64encode(self.public_key.public_bytes_raw())

    def make_input(self, tx_id, output_index):
        output_tx = None
        for tx in find_utxos():
            if tx.id == tx_id:
                output_tx = tx
                break
        if not output_tx:
            return
        signature = self.private_key.sign(output_tx.encode())
        return TXInput(
            tx_id=tx_id,
            output_index=output_index,
            unlock_script=signature + self.public_key.public_bytes_raw()
        )

    def make_output(self, input_index):
        return TXOutput(
            input_index=input_index,
            lock_script=self.address
        )

    def add(self):
        outputs = [self.make_output(0)]
        tx = make_tx([], 'r', outputs)
        chain.append(tx)

    def move(self, direction: str):
        last_player_tx = find_player_last_tx(self.address)
        if not last_player_tx:
            return
        inputs = [
            self.make_input(
                tx_id=last_player_tx.id,
                output_index=last_player_tx.outputs.index(out)
            )
            for out in last_player_tx.outputs
            if out.lock_script == self.address
        ]
        outputs = [self.make_output(0)]
        tx = make_tx(inputs=inputs, data=direction, outputs=outputs)
        chain.append(tx)
        return tx

    def get_player_pos(self, player_id: str):
        x, y = 0, 0
        for tx in chain:
            if any([out.lock_script == player_id for out in tx.outputs]):
                if tx.data in ('l', 'r'):
                    x += 1 if tx.data == 'r' else -1
                if tx.data in ('u', 'd'):
                    y += 1 if tx.data == 'd' else -1
        return x, y

    def pick_object(self):
        object_tx = None
        pl_pos = self.get_player_pos(self.address)
        for tx in find_utxos():
            if sha256(str(pl_pos).encode()).digest() == tx.outputs[0].lock_script:
                object_tx = tx
                break
        if not object_tx:
            print("Need tx not found")
            return

        pl_move_tx = find_player_last_tx(self.address)
        inputs = [
            self.make_input(tx_id=pl_move_tx.id, output_index=0),
            self.make_input(tx_id=object_tx.id, output_index=0)
        ]
        outputs = [self.make_output(0), self.make_output(1)]
        outputs[1].lock_script += b'a'
        tx = make_tx(inputs=inputs, data=object_tx.data, outputs=outputs)
        chain.append(tx)
        return tx

    def get_player_inventory(self, player_id):
        object_txs = []
        for tx in find_utxos():
            if any([out.lock_script == player_id for out in tx.outputs]) and tx.data not in 'lrud':
                object_txs.append(tx)
        return [tx.data for tx in object_txs]


pl1 = PlayerService()
pl2 = PlayerService()
pl1.add()
pl2.add()
add_object('b', (3, 2))
add_object('c', (3, 2))
add_object('f', (3, 2))
pl1.move('r')
pl1.move('r')
pl1.move('d')
pl1.move('d')
pick1_tx = pl1.pick_object()
pick2_tx = pl1.pick_object()
print(pl1.get_player_inventory(pl1.address))

pl2.move('r')
pl2.move('r')
pl2.move('d')
pl2.move('d')
pick_tx = pl2.pick_object()
print(pl1.get_player_inventory(pl2.address))
