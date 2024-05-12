from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class Actor:
    @staticmethod
    def new_id():
        return str(uuid4())

    id: str = field(default_factory=new_id)


@dataclass
class StaticObject:
    position: tuple[int, int]
    object_id: str

