from app.backend.repository import ActorEvent
from app.backend.database.models import ValidateError
from app.api.schemas import ActorPositionSchema
from app.api.schemas import ActorInfoSchema

from fastapi import HTTPException


class ActorService:
    backend_repository = None

    def __init__(self):
        pass

    def make(self, schema):
        try:
            return self.backend_repository.make_actor(**schema.model_dump())
        except ValidateError:
            raise HTTPException(404)

    def handle_event(self, schema):
        for event in ActorEvent:
            if event.name == schema.event.name:
                return self.backend_repository.handle_event(event=event, actor_token=schema.token, **schema.args)

    def get_actors(self) -> list[ActorPositionSchema]:
        positions = self.backend_repository.get_actors_positions()
        ret = []
        for pos, actor in positions.items():
            ret.append(ActorPositionSchema(position=pos, address=actor.id))
        return ret

    def get_actor(self, address: str) -> ActorInfoSchema:
        pos = self.backend_repository.get_actor_position(address)
        inv = self.backend_repository.get_actor_picked(address)
        return ActorInfoSchema(position=pos, inventory=inv, address=address)

