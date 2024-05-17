import pygame as pg
from pathlib import Path
import random

assets_path = Path('../assets/')
background_images = [
    [30, pg.image.load(assets_path / 'grass_top2.png')],
    [1, pg.image.load(assets_path / 'grass_with_a_ozero.png')],
    [1, pg.image.load(assets_path / 'Land_with_a_river.png')],

]
for i in range(len(background_images)):
    background_images[i][1] = pg.transform.scale(background_images[i][1], (50, 50))

_grades = (90, 180, 270, 0)


class BackgroundTile(pg.sprite.Sprite):
    def __init__(self, coordinates, *groups):
        super().__init__(*groups)
        self.image = random.choices(
                list(map(lambda i: i[1], background_images)),
                list(map(lambda i: i[0], background_images))
        )[0].copy()
        self.image = pg.transform.rotate(self.image, random.choice(_grades))
        self.rect = self.image.get_rect(topleft=coordinates)

