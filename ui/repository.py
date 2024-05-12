import pygame as pg
from backend.repository import BackendRepository


SCREEN_SIZE = (500, 500)
SCALE = 50
pg.init()


class UIRepository:
    def __init__(self, backend_rep):
        self.screen = pg.display.set_mode(SCREEN_SIZE)
        self.running = True
        self.sprites = pg.sprite.Group()
        self.clock = pg.time.Clock()

        self.backend_rep = backend_rep

    def run(self):
        while self.running:
            self.clock.tick(2)

            for e in pg.event.get():
                if e.type == pg.QUIT:
                    self.running = False

            self.screen.fill((230, 230, 230))
            
            positions = self.backend_rep.get_actors_positions()
            for position in positions.keys():
                self.screen.fill(
                    (255, 0, 0),
                    (
                        (position[0] * SCALE, position[1] * SCALE),
                        (SCALE, SCALE)
                    )
                )

            objects = self.backend_rep.get_static_objects_positions()
            for obj in objects:
                position = obj.position
                self.screen.fill(
                    (255, 255, 0),
                    (
                        (position[0] * SCALE, position[1] * SCALE),
                        (SCALE, SCALE)
                    )
                )

            pg.display.flip()

