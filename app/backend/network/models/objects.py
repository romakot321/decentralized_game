from pydantic import BaseModel, Field, AliasChoices
from pydantic.networks import IPvAnyAddress
import struct
import datetime as dt

from app.backend.utils import asdict


class NodeInfo(BaseModel):
    services: list[str]


class Node(BaseModel):
    ip: IPvAnyAddress
    port: int
    #info: NodeInfo | None = None
    _HEADER_SIZE: int = struct.calcsize('IH')

    def encode(self):
        return struct.pack('>IH', int(self.ip), self.port)

    @classmethod
    def decode(cls, data: bytes):
        ip, port = struct.unpack('>IH', data)
        return cls(ip=ip, port=port)

    def __hash__(self):
        return hash(self.model_dump_json())


class NetworkTXInput(BaseModel):
    tx_id: str
    output_index: int
    unlock_script: bytes
    _HEADER_SIZE: int = struct.calcsize('>64sHQ')

    @property
    def ENCODED_SIZE(self) -> int:
        return self.HEADER_SIZE + len(unlock_script)

    def encode(self) -> bytes:
        return struct.pack(
            f'>64sHQ{len(self.unlock_script)}s',
            self.tx_id.encode(),
            self.output_index,
            len(self.unlock_script),
            self.unlock_script
        )

    @classmethod
    def decode(cls, data: bytes):
        tx_id, output_index, script_size = struct.unpack('>64sHQ', data[:cls._HEADER_SIZE.default])
        return cls(
            tx_id=tx_id.decode(),
            output_index=output_index,
            unlock_script=data[cls._HEADER_SIZE.default:]
        )


class NetworkTXOutput(BaseModel):
    input_index: int
    value: bytes
    lock_script: bytes
    _HEADER_SIZE: int = struct.calcsize('>HQ')

    def encode(self) -> bytes:
        return struct.pack(
            f'>HQ{len(self.value)}sQ{len(self.lock_script)}s',
            self.input_index,
            len(self.value),
            self.value,
            len(self.lock_script),
            self.lock_script
        )

    @classmethod
    def decode(cls, data: bytes):
        input_index, value_size = struct.unpack('>HQ', data[:cls._HEADER_SIZE.default])
        value = data[cls._HEADER_SIZE.default:cls._HEADER_SIZE.default + value_size]
        return cls(
            input_index=input_index,
            value=value,
            lock_script=data[cls._HEADER_SIZE.default + value_size + 8:]
        )


class NetworkTransaction(BaseModel):
    outputs: list[NetworkTXOutput]
    inputs: list[NetworkTXInput]
    _HEADER_SIZE: int = struct.calcsize('>Q')

    def encode(self) -> bytes:
        outputs_encoded = b''.join([out.encode() for out in self.outputs])
        inputs_encoded = b''.join([inp.encode() for inp in self.inputs])
        return struct.pack(
            f'>Q{len(outputs_encoded)}sQ{len(inputs_encoded)}s',
            len(outputs_encoded),
            outputs_encoded,
            len(inputs_encoded),
            inputs_encoded
        )

    @classmethod
    def decode(cls, data: bytes):
        (outputs_size,) = struct.unpack('>Q', data[:cls._HEADER_SIZE.default])
        outputs = []
        inputs = []
        i = cls._HEADER_SIZE.default
        while i < outputs_size:
            _, value_size = struct.unpack('>HQ', data[i:i + NetworkTXOutput._HEADER_SIZE.default])
            script_size = data[i + NetworkTXOutput._HEADER_SIZE.default + value_size:i + NetworkTXOutput._HEADER_SIZE.default + value_size + 8]
            (script_size,) = struct.unpack('>Q', script_size)
            output_size = NetworkTXOutput._HEADER_SIZE.default + value_size + script_size + 8
            outputs.append(NetworkTXOutput.decode(data[i:i + output_size]))
            i += output_size
        (inputs_size,) = struct.unpack('>Q', data[i:i + cls._HEADER_SIZE.default])
        i += cls._HEADER_SIZE.default
        while i - outputs_size < inputs_size:
            _, _, script_size = struct.unpack('>64sHQ', data[i:i + NetworkTXInput._HEADER_SIZE.default])
            input_size = NetworkTXInput._HEADER_SIZE.default + script_size
            inputs.append(NetworkTXInput.decode(data[i:i + input_size]))
            i += input_size
        return cls(inputs=inputs, outputs=outputs)

    @classmethod
    def from_db_model(cls, model):
        state = asdict(model)
        return cls(**state)


class NetworkBlock(BaseModel):
    timestamp: dt.datetime
    nounce: int
    prev_hash: str = Field(validation_alias=AliasChoices('previous_hash', 'prev_hash'))
    transactions: list[NetworkTransaction]
    _HEADER_SIZE: int = struct.calcsize('>dQ64sQ')

    def encode(self):
        txs_encoded = b''.join([tx.encode() for tx in self.transactions])
        return struct.pack(
            f'>dQ64sQ{len(txs_encoded)}s',
            self.timestamp.timestamp(),
            self.nounce,
            self.prev_hash.encode(),
            len(txs_encoded),
            txs_encoded
        )

    @classmethod
    def decode(cls, data: bytes):
        timestamp, nounce, prev_hash, txs_size = struct.unpack('>dQ64sQ', data[:88])
        transactions = []
        i = 88
        tx_header = NetworkTransaction._HEADER_SIZE.default
        while i - 88 < txs_size:
            (outputs_size,) = struct.unpack('>Q', data[i:i + tx_header])
            (inputs_size,) = struct.unpack(
                '>Q',
                data[
                    i + tx_header + outputs_size
                    :
                    i + tx_header * 2 + outputs_size
                ]
            )
            transactions.append(NetworkTransaction.decode(data[i:i + tx_header * 2 + outputs_size + inputs_size]))
            i += tx_header * 2 + outputs_size + inputs_size
        return cls(
            timestamp=dt.datetime.fromtimestamp(timestamp),
            nounce=nounce,
            prev_hash=prev_hash.decode(),
            transactions=transactions
        )

    @classmethod
    def from_db_model(cls, model):
        state = asdict(model)
        #print(state)
        #state['transactions'] = [asdict(tx) for tx in state['transactions']]
        #for i in range(len(state['transactions'])):
        #    state['transactions'][i]['outputs'] = [asdict(out) for out in state['transactions'][i]['outputs']]
        #    state['transactions'][i]['inputs'] = [asdict(inp) for inp in state['transactions'][i]['inputs']]
        return cls(**state)


if __name__ == '__main__':
    inputs = [
        NetworkTXInput(output_index=0, tx_id='a' * 64, unlock_script=b'a'),
        NetworkTXInput(output_index=1, tx_id='b' * 64, unlock_script=b'ab'),
    ]
    outputs = [
        NetworkTXOutput(input_index=0, value=b'0:0', lock_script=b'c'),
        NetworkTXOutput(input_index=1, value=b'3:adfa', lock_script=b'cb'),
    ]
    txs = [
        NetworkTransaction(inputs=inputs, outputs=outputs),
        NetworkTransaction(inputs=inputs[:1], outputs=outputs[:1])
    ]
    block = NetworkBlock(timestamp=dt.datetime.now(), nounce=1, prev_hash='c' * 64, transactions=txs)
    block2 = NetworkBlock(timestamp=dt.datetime.now(), nounce=2, prev_hash='d' * 64, transactions=txs[:1])
    encoded = block.encode() + block2.encode()

    blocks = []
    i = 0
    while i < len(encoded):
        _, _, _, txs_size = struct.unpack('>dQ64sQ', encoded[i:i + NetworkBlock._HEADER_SIZE.default])
        block_size = NetworkBlock._HEADER_SIZE.default + txs_size
        blocks.append(NetworkBlock.decode(encoded[i:i + block_size]))
        i += block_size

    encoded_block = NetworkBlock.decode(encoded)
    print(encoded_block)
    print(block == encoded_block)
