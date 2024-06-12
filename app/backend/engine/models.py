from dataclasses import dataclass, field
from uuid import uuid4
from enum import Enum


@dataclass
class Actor:
    id: str
    token: str | None = None


@dataclass
class StaticObject:
    position: tuple[int, int]
    object_id: int


@dataclass
class Biome:
    name: str
    min_height: int
    max_height: int


class Biomes(Enum):
    plain = Biome(name='plain', min_height=-10000, max_height=1)
    mountain = Biome(name='mountain', min_height=2, max_height=10000)

    @classmethod
    def from_height(cls, height: int) -> Biome:
        for biome_name in cls._member_names_:
            biome = getattr(cls, biome_name)
            if height in range(biome.value.min_height, biome.value.max_height + 1):
                return biome.value

