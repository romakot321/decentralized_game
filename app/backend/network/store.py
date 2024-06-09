from app.backend.network.models import Node
import datetime as dt


class NodesStore:
    def __init__(self):
        self._nodes: dict[Node, dt.datetime] = {}

    def store(self, node: tuple | Node):
        if isinstance(node, tuple):
            node = Node(ip=node[0], port=node[1])
        self._nodes[node] = dt.datetime.now()

    def get(self) -> list[Node]:
        for node, last_seen in self._nodes.items():
            if (dt.datetime.now() - last_seen).seconds > 60 * 60 * 3:  # 3 hours
                self._nodes.pop(node)
        return list(self._nodes.keys())

