import pygame as pg
from app.ui.backend_service import BackendService
from app.ui.sprites import BackgroundTile
from app.ui.sprites import InventoryPane
import datetime as dt
import os


SCREEN_SIZE = (550, 550)
SCALE = 50
pg.init()
pg.font.init()


class UIRepository:
    COOLDOWN = 0.02

    def __init__(self, backend_service):
        self.screen = None
        self.running = True
        self.sprites = pg.sprite.Group()
        self.clock = pg.time.Clock()
        self.font = pg.font.SysFont('Times New Roman', 14)

        self.backend_service = backend_service
        
        self._last_action = dt.datetime.now()
        self.sprites = pg.sprite.Group()
        self.ui_sprites = pg.sprite.Group()

        self._chunks_border = pg.rect.Rect(
            -SCREEN_SIZE[0] * 5,
            -SCREEN_SIZE[1] * 5,
            SCREEN_SIZE[0] * 10,
            SCREEN_SIZE[1] * 10
        )

    def get_auth_pair(self) -> tuple[str, str]:
        keys = os.listdir('keys')
        for i, key in enumerate(keys):
            print(i + 1, key[:16])
        address = input("Address number: ")
        password = input("Password: ")
        if address.isdigit():
            address = keys[int(address) - 1]
        else:
            address = None
        return (password, address)

    def init(self):
        self.screen = pg.display.set_mode(SCREEN_SIZE)
        for y in range(self._chunks_border.top, self._chunks_border.bottom, SCALE):
            for x in range(self._chunks_border.left, self._chunks_border.right, SCALE):
                chunk_x, chunk_y = x // SCALE // 5, y // SCALE // 5
                biome = self.backend_service.get_chunk_info(chunk_x, chunk_y)
                self.sprites.add(BackgroundTile(coordinates=(x, y), biome=biome))
        self.ui_sprites.add(InventoryPane(SCREEN_SIZE, self.backend_service))
        password, address = self.get_auth_pair()
        self.backend_service.init(password, address)

    def generate_chunks(self, left=False, right=False, top=False, bottom=False):
        expand_bias = 5 * SCALE
        if top:
            for y in range(self._chunks_border.top - expand_bias, self._chunks_border.top, SCALE):
                for x in range(self._chunks_border.left - expand_bias, self._chunks_border.right + expand_bias, SCALE):
                    chunk_x, chunk_y = x // SCALE // 5, y // SCALE // 5
                    biome = self.backend_service.get_chunk_info(chunk_x, chunk_y)
                    self.sprites.add(BackgroundTile(coordinates=(x, y), biome=biome))
            for obj in self.sprites.sprites():
                if obj.rect.y in range(self._chunks_border.bottom - expand_bias, self._chunks_border.bottom, SCALE):
                    self.sprites.remove(obj)
        if left:
            for y in range(self._chunks_border.top, self._chunks_border.bottom, SCALE):
                for x in range(self._chunks_border.left - expand_bias, self._chunks_border.left, SCALE):
                    chunk_x, chunk_y = x // SCALE // 5, y // SCALE // 5
                    biome = self.backend_service.get_chunk_info(chunk_x, chunk_y)
                    self.sprites.add(BackgroundTile(coordinates=(x, y), biome=biome))
            for obj in self.sprites.sprites():
                if obj.rect.x in range(self._chunks_border.right - expand_bias, self._chunks_border.right, SCALE):
                    self.sprites.remove(obj)
        if right:
            for y in range(self._chunks_border.top, self._chunks_border.bottom, SCALE):
                for x in range(self._chunks_border.right, self._chunks_border.right + expand_bias, SCALE):
                    chunk_x, chunk_y = x // SCALE // 5, y // SCALE // 5
                    biome = self.backend_service.get_chunk_info(chunk_x, chunk_y)
                    self.sprites.add(BackgroundTile(coordinates=(x, y), biome=biome))
            for obj in self.sprites.sprites():
                if obj.rect.x in range(self._chunks_border.left, self._chunks_border.left + expand_bias, SCALE):
                    self.sprites.remove(obj)
        if bottom:
            for y in range(self._chunks_border.bottom, self._chunks_border.bottom + expand_bias, SCALE):
                for x in range(self._chunks_border.left - expand_bias, self._chunks_border.right + expand_bias, SCALE):
                    chunk_x, chunk_y = x // SCALE // 5, y // SCALE // 5
                    biome = self.backend_service.get_chunk_info(chunk_x, chunk_y)
                    self.sprites.add(BackgroundTile(coordinates=(x, y), biome=biome))
            for obj in self.sprites.sprites():
                if obj.rect.y in range(self._chunks_border.top, self._chunks_border.top + expand_bias, SCALE):
                    self.sprites.remove(obj)
        self._chunks_border = pg.rect.Rect(
            self._chunks_border.left - expand_bias * left + expand_bias * right,
            self._chunks_border.top - expand_bias * top + expand_bias * bottom,
            self._chunks_border.width,
            self._chunks_border.height
        )

    def can_do_action(self):
        return (dt.datetime.now() - self._last_action).microseconds >= self.COOLDOWN * 10 ** 6

    def _draw_actors(self):
        positions = self.backend_service.get_actors_positions()
        my_actor_position = self.backend_service.get_my_actor_position()
        my_actor_position = (my_actor_position[0] - (SCREEN_SIZE[0] // SCALE // 2),
                             my_actor_position[1] - (SCREEN_SIZE[1] // SCALE // 2))
        for position in positions.keys():
            position = (position[0] - my_actor_position[0], position[1] - my_actor_position[1])
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
        key_down = None
        while self.running:
            self.clock.tick(20)

            for e in pg.event.get():
                if e.type == pg.QUIT:
                    self.running = False
                elif e.type == pg.KEYDOWN:
                    if e.key == pg.K_ESCAPE:
                        self.running = False
                    else:
                        key_down = e.key
                elif e.type == pg.KEYUP:
                    if e.key == key_down:
                        key_down = None
                elif e.type == pg.MOUSEBUTTONDOWN:
                    if e.button == 1:
                        cursor_pos = pg.mouse.get_pos()
                        self._handle_ui_click(cursor_pos)
            if key_down and self.can_do_action():
                if self.backend_service.handle_actor_action(key_down):
                    self._last_action = dt.datetime.now()

            self.screen.fill((230, 230, 230))
            my_actor_position = self.backend_service.get_my_actor_position()
            my_actor_position = (my_actor_position[0] + (SCREEN_SIZE[0] // SCALE // 2),
                                 my_actor_position[1] + (SCREEN_SIZE[1] // SCALE // 2))
            my_actor_position = (my_actor_position[0] * SCALE, my_actor_position[1] * SCALE)
            if my_actor_position[0] < self._chunks_border.left:
                self.generate_chunks(left=True)
            if my_actor_position[0] > self._chunks_border.right - SCREEN_SIZE[0]:
                self.generate_chunks(right=True)
            if my_actor_position[1] > self._chunks_border.bottom - SCREEN_SIZE[1]:
                self.generate_chunks(bottom=True)
            if my_actor_position[1] < self._chunks_border.top:
                self.generate_chunks(top=True)
            for sprite in self.sprites:
                pos = (sprite.rect.x - my_actor_position[0], sprite.rect.y - my_actor_position[1])
                self.screen.blit(sprite.image, pos)

            self._draw_objects()
            self._draw_actors()

            self._draw_cooldown()
            self._draw_inventory()

            pg.display.flip()
        pg.exit()

