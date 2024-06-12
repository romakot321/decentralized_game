from app.ui.models import Collectable, Actor, ActorEvent
import pygame as pg
import requests
import os
from enum import Enum
from pydantic import BaseModel


class Biome(BaseModel):
    name: str
    min_height: int
    max_height: int


class Biomes(Enum):
    plain = Biome(name='plain', min_height=-10000, max_height=1)
    mountain = Biome(name='mountain', min_height=2, max_height=10000)


class BackendService:
    node_address = os.getenv("NODE_ADDRESS", '127.0.0.1:8000')
    node_url = 'http://' + node_address.rstrip('/')

    def __init__(self):
        self.actor: Actor = None

    def _do_post_request(self, path: str, **data) -> dict:
        resp = requests.post(self.node_url + '/' + path.lstrip('/'), json=data)
        assert resp.status_code // 100 == 2, resp.text
        return resp.json()

    def _do_get_request(self, path: str, **data):
        resp = requests.get(self.node_url + "/" + path.lstrip('/'), data=data)
        assert resp.status_code // 100 == 2, resp.text
        return resp.json()

    def init(self, password: str, address: str = None):
        request_data = {'password': password}
        if address:
            request_data['address'] = address
        actor_state = self._do_post_request('actor', **request_data)
        self.actor = Actor.model_validate(actor_state)

    def drop_item(self, collectable_id: str):
        self._do_post_request('actor/event', token=self.actor.token, event=ActorEvent.DROP.value, args={'object_id': collectable_id})

    def get_actors_positions(self) -> list[Actor]:
        actors_states = self._do_get_request('actor')
        return [Actor.model_validate(actor) for actor in actors_states] 
    
    def get_my_actor_position(self) -> tuple[int, int]:
        actor_state = self._do_get_request(f'actor/{self.actor.id}')
        return Actor.model_validate(actor_state).position

    def get_static_objects_positions(self):
        objects_states = self._do_get_request('static')
        return [Collectable.model_validate(state) for state in objects_states]

    def get_chunk_info(self, chunk_x, chunk_y):
        return Biomes.plain
        return self.back_rep.get_chunk_info(chunk_x, chunk_y)

    def get_actor_inventory(self) -> list[Collectable]:
        actor_state = self._do_get_request(f'actor/{self.actor.id}')
        items = Actor.model_validate(actor_state).inventory
        return [
            Collectable(id=i)
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
            self._do_post_request('actor/event', token=self.actor.token, event=event.value)
            return True
        return False

