import pygame as pg
from pathlib import Path
import random

assets_path = Path('../assets/')
background_images = {
    'plain': [
        [30, pg.image.load(assets_path / 'grass_top2.png')],
        [1, pg.image.load(assets_path / 'grass_with_a_ozero.png')],
        [1, pg.image.load(assets_path / 'Land_with_a_river.png')],
    ],
    'mountain': [
        [1, pg.image.load(assets_path / 'stone_top.png')]
    ]
}

for biome_name, sprites in background_images.items():
    for i in range(len(sprites)):
        background_images[biome_name][i][1] = pg.transform.scale(background_images[biome_name][i][1], (50, 50))

_grades = (90, 180, 270, 0)


class BackgroundTile(pg.sprite.Sprite):
    def __init__(self, coordinates, biome, *groups):
        super().__init__(*groups)
        self.image = random.choices(
                list(map(lambda i: i[1], background_images[biome.name])),
                list(map(lambda i: i[0], background_images[biome.name]))
        )[0].copy()
        self.image = pg.transform.rotate(self.image, random.choice(_grades))
        self.rect = self.image.get_rect(topleft=coordinates)


class UISprite(pg.sprite.Sprite):
    def __init__(self, screen_size, backend_service, *groups):
        super().__init__(*groups)
        self.screen_size = screen_size
        self.backend_service = backend_service

    def update(self, backend_service):
        pass

    def handle_click(self, click_pos: tuple[int, int]):
        pass


class InventoryPane(UISprite):
    def __init__(self, screen_size, backend_service, *groups):
        super().__init__(screen_size, backend_service, *groups)
        self.image = pg.surface.Surface((screen_size[0] * 0.3, screen_size[1] * 0.08))
        self.image.set_alpha(220)
        self.rect = self.image.get_rect(topleft=(screen_size[0] - self.image.get_width(), 0))

        self._item_image_size = (self.image.get_height(),) * 2
        self._inventory = []

    def _update_inventory(self):
        inventory: list[Collectable] = self.backend_service.get_actor_inventory()
        if len(self._inventory) == len(inventory):
            return

        stored_ids = [i[0].object_id for i in self._inventory]
        self._inventory = [
            (
                item,
                (
                    int(item.object_id[:2], 16),
                    int(item.object_id[2:4], 16),
                    int(item.object_id[4:6], 16)
                )
            )
            for item in inventory
        ]
        
    def handle_click(self, click_pos: tuple):
        x = 0
        for item, _ in self._inventory:
            if click_pos[0] in range(x, x + self._item_image_size[0] + 5):
                self.backend_service.drop_item(item.object_id)
                break
            x += self._item_image_size[0] + 5

    def update(self):
        self._update_inventory()
        self.image.fill((20, 20, 20))
        x = 0
        for item, item_color in self._inventory:
            item_image = pg.surface.Surface(self._item_image_size)
            item_image.fill(item_color)
            self.image.blit(item_image, (x, 0))
            x += self._item_image_size[0] + 5

