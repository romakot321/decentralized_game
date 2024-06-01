from app.backend.repository import ActorEvent
from app.ui.models import Collectable
import pygame as pg


class BackendService:
    def __init__(self, backend_repository):
        self.back_rep = backend_repository
        self.actor = None

    def init(self):
        self.actor = self.back_rep.make_actor()

    def get_actors_positions(self):
        return self.back_rep.get_actors_positions()
    
    def get_my_actor_position(self) -> tuple[int, int]:
        return self.back_rep.get_actor_position(self.actor.id)

    def get_static_objects_positions(self):
        return self.back_rep.get_static_objects_positions()

    def get_actor_inventory(self) -> list[Collectable]:
        items = self.back_rep.get_actor_picked(self.actor.id)
        return [
            Collectable(object_id=i)
            for i in items
        ]

    def handle_actor_action(self, key):
        event = None
        if key == pg.K_w:
            event = ActorEvent.MOVE_UP
        elif key == pg.K_d:
            event = ActorEvent.MOVE_RIGHT
        elif key == pg.K_a:
            event = ActorEvent.MOVE_LEFT
        elif key == pg.K_s:
            event = ActorEvent.MOVE_DOWN
        elif key == pg.K_p:
            event = ActorEvent.PICK

        if event:
            self.back_rep.handle_event(event, self.actor.id)
            return True
        return False

