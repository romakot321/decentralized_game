import pygame as pg
from app.ui.backend_service import BackendService
from app.ui.sprites import BackgroundTile
from app.ui.sprites import InventoryPane
import datetime as dt


SCREEN_SIZE = (500, 500)
SCALE = 50
pg.init()
pg.font.init()


class UIRepository:
    COOLDOWN = 0.2

    def __init__(self, backend_service):
        self.screen = pg.display.set_mode(SCREEN_SIZE)
        self.running = True
        self.sprites = pg.sprite.Group()
        self.clock = pg.time.Clock()
        self.font = pg.font.SysFont('Times New Roman', 14)

        self.backend_service = backend_service
        
        self._last_action = dt.datetime.now()
        self.sprites = pg.sprite.Group()
        self.ui_sprites = pg.sprite.Group()

        self.init()

    def init(self):
        for y in range(-(SCREEN_SIZE[1] * 10), SCREEN_SIZE[1] * 10, SCALE):
            for x in range(-SCREEN_SIZE[0] * 10, SCREEN_SIZE[0] * 10, SCALE):
                self.sprites.add(BackgroundTile(coordinates=(x, y)))
        self.ui_sprites.add(InventoryPane(SCREEN_SIZE, self.backend_service))
        self.backend_service.init()

    def can_do_action(self):
        return (dt.datetime.now() - self._last_action).microseconds >= self.COOLDOWN * 10 ** 6

    def _draw_actors(self):
        positions = self.backend_service.get_actors_positions()
        my_actor_position = self.backend_service.get_my_actor_position()
        my_actor_position = (my_actor_position[0] + (SCREEN_SIZE[0] // SCALE // 2),
                             my_actor_position[1] + (SCREEN_SIZE[1] // SCALE // 2))
        for position in positions.keys():
            #position = (position[0] - my_actor_position[0], position[1] - my_actor_position[1])
            position = (my_actor_position[0] - position[0], my_actor_position[1] - position[1])
            self.screen.fill(
                (255, 0, 0),
                (
                    (position[0] * SCALE, position[1] * SCALE),
                    (SCALE, SCALE)
                )
            )

    def _draw_objects(self):
        objects = self.backend_service.get_static_objects_positions()
        my_actor_position = self.backend_service.get_my_actor_position()
        my_actor_position = (my_actor_position[0] - (SCREEN_SIZE[0] // SCALE // 2),
                             my_actor_position[1] - (SCREEN_SIZE[1] // SCALE // 2))
        for obj in objects:
            position = obj.position
            position = (position[0] - my_actor_position[0], position[1] - my_actor_position[1])
            self.screen.fill(
                (
                    int(obj.object_id[:2], 16),
                    int(obj.object_id[2:4], 16),
                    int(obj.object_id[4:6], 16)
                ),
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
        self.ui_sprites.update()
        self.ui_sprites.draw(self.screen)

    def _handle_ui_click(self, click_point: tuple[int, int]):
        for ui_sprite in self.ui_sprites:
            if ui_sprite.rect.collidepoint(click_point):
                ui_sprite.handle_click(
                    (
                        click_point[0] - ui_sprite.rect.left,
                        click_point[1] - ui_sprite.rect.top
                    )
                )  # Transform point to ui rect

    def run(self):
        while self.running:
            self.clock.tick(30)

            for e in pg.event.get():
                if e.type == pg.QUIT:
                    self.running = False
                elif e.type == pg.KEYUP and self.can_do_action():
                    if e.key == pg.K_ESCAPE:
                        self.running = False
                    elif self.backend_service.handle_actor_action(e.key):
                        self._last_action = dt.datetime.now()
                elif e.type == pg.MOUSEBUTTONDOWN:
                    if e.button == 1:
                        cursor_pos = pg.mouse.get_pos()
                        self._handle_ui_click(cursor_pos)

            self.screen.fill((230, 230, 230))
            my_actor_position = self.backend_service.get_my_actor_position()
            my_actor_position = (my_actor_position[0] + (SCREEN_SIZE[0] // SCALE // 2),
                                 my_actor_position[1] + (SCREEN_SIZE[1] // SCALE // 2))
            for sprite in self.sprites:
                pos = (sprite.rect.x - my_actor_position[0] * SCALE, sprite.rect.y - my_actor_position[1] * SCALE)
                self.screen.blit(sprite.image, pos)

            self._draw_objects()
            self._draw_actors()

            self._draw_cooldown()
            self._draw_inventory()

            pg.display.flip()
        pg.exit()

