from app.backend.network.models import Message, Command
from app.backend.network.models import BlocksPayload, NodesStorePayload
from app.backend.network.models import Payload


class ResponseWorker:
    def handle(self, data) -> Payload | None:
        msg = Message.from_bytes(data)
        match msg.command:
            case Command.nodes_store:
                return NodesStorePayload.decode(msg.payload)
            case Command.blocks:
                return BlocksPayload.decode(msg.payload)
            case Command.error:
                if msg.payload == b'OK':
                    return
                print(f"[ERROR] {msg.payload.decode()}")
