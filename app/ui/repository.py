import pygame as pg
from app.ui.backend_service import BackendService
from app.ui.sprites import BackgroundTile
import datetime as dt


SCREEN_SIZE = (500, 500)
SCALE = 50
pg.init()
pg.font.init()


class UIRepository:
    COOLDOWN = 1

    def __init__(self, backend_service):
        self.screen = pg.display.set_mode(SCREEN_SIZE)
        self.running = True
        self.sprites = pg.sprite.Group()
        self.clock = pg.time.Clock()
        self.font = pg.font.SysFont('Times New Roman', 14)

        self.backend_service = backend_service
        
        self._last_action = dt.datetime.now()
        self.sprites = pg.sprite.Group()
        for y in range(0, SCREEN_SIZE[1], SCALE):
            for x in range(0, SCREEN_SIZE[0], SCALE):
                self.sprites.add(BackgroundTile(coordinates=(x, y)))

    def can_do_action(self):
        return (dt.datetime.now() - self._last_action).seconds >= self.COOLDOWN

    def _draw_actors(self):
        positions = self.backend_service.get_actors_positions()
        for position in positions.keys():
            self.screen.fill(
                (255, 0, 0),
                (
                    (position[0] * SCALE, position[1] * SCALE),
                    (SCALE, SCALE)
                )
            )

    def _draw_objects(self):
        objects = self.backend_service.get_static_objects_positions()
        for obj in objects:
            position = obj.position
            self.screen.fill(
                (255, 255, 0),
                (
                    (position[0] * SCALE, position[1] * SCALE),
                    (SCALE, SCALE)
                )
            )

    def _draw_cooldown(self):
        delta_time = (dt.datetime.now() - self._last_action)
        x_size = (delta_time.seconds * 10 ** 6 + delta_time.microseconds) / (self.COOLDOWN * 10 ** 6)
        x_size = SCREEN_SIZE[0] * x_size
        pg.draw.rect(self.screen, (0, 71, 171), (0, SCREEN_SIZE[1] - 7, x_size, SCREEN_SIZE[1]))

    def _draw_inventory(self):
        items = self.backend_service.get_actor_inventory()
        curr_y = 5
        for item in items:
            text = self.font.render(item, False, (0, 0, 0))
            self.screen.blit(text, (10, curr_y))
            curr_y += self.font.get_height() + 5

    def run(self):
        while self.running:
            self.clock.tick(15)

            for e in pg.event.get():
                if e.type == pg.QUIT:
                    self.running = False
                elif e.type == pg.KEYUP and self.can_do_action():
                    if e.key == pg.K_ESCAPE:
                        self.running = False
                    elif self.backend_service.handle_actor_action(e.key):
                        self._last_action = dt.datetime.now()

            self.screen.fill((230, 230, 230))
            self.sprites.draw(self.screen)

            self._draw_objects()
            self._draw_actors()
            self._draw_cooldown()
            self._draw_inventory()

            pg.display.flip()
        pg.exit()

