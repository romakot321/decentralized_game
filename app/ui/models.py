from pydantic import BaseModel, Field, AliasChoices
from enum import Enum


class Collectable(BaseModel):
    id: str
    position: tuple[int, int] | None = None


class Actor(BaseModel):
    id: str = Field(validation_alias=AliasChoices('address', 'id'))
    position: tuple[int, int] | None = None
    inventory: list[str] | None = None
    token: str | None = None


class ActorEvent(Enum):
    MOVE_UP = 'up'
    MOVE_RIGHT = 'right'
    MOVE_LEFT = 'left'
    MOVE_DOWN = 'down'
    PICK = 'pick'
    DROP = 'drop'

