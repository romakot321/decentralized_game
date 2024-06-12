from pydantic import BaseModel, Field, AliasChoices
from enum import Enum


class Event(str, Enum):
    MOVE_UP = 'up'
    MOVE_RIGHT = 'right'
    MOVE_LEFT = 'left'
    MOVE_DOWN = 'down'
    PICK = 'pick'
    DROP = 'drop'
    

class ActorMakeSchema(BaseModel):
    password: str
    address: str | None = None


class ActorSchema(BaseModel):
    address: str = Field(validation_alias=AliasChoices('id', 'address'))
    token: str | None = None


class ActorEventSchema(BaseModel):
    token: str
    event: Event
    args: dict = {}


class ActorPositionSchema(BaseModel):
    address: str
    position: tuple[int, int]


class ActorInfoSchema(BaseModel):
    address: str
    position: tuple[int, int]
    inventory: list[str]

