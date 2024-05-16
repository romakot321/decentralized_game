from app.backend.repository import ActorEvent
import pygame as pg


class BackendService:
    def __init__(self, backend_repository):
        self.back_rep = backend_repository

    def get_actors_positions(self):
        return self.back_rep.get_actors_positions()

    def get_static_objects_positions(self):
        return self.back_rep.get_static_objects_positions()

    def get_actor_inventory(self):
        return self.back_rep.get_actor_picked()

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

        if event:
            self.back_rep.handle_event(event)
            return True
        return False

