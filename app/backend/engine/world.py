from perlin_noise import PerlinNoise
from app.backend.engine.models import Biomes, Biome


class WorldService:
    amp = 10
    period = 20
    octaves = 2

    def __init__(self, world_size: int):
        self.world_size = world_size
        self._new_size_bias = world_size + max(2, world_size // 10)
        self._landscale = [[0] * world_size for _ in range(world_size)]
        self.seed = None

    def init(self, seed: int):
        noise = PerlinNoise(octaves=self.octaves, seed=seed)
        self.seed = seed

        for pos in range(self.world_size ** 2):
            x = int(pos / self.world_size)
            y = int(pos % self.world_size)
            if self._landscale[x][y] != 0:
                continue
            height = int(noise([x / self.period, y / self.period]) * self.amp)
            self._landscale[x][y] = height

    def generate_new(self, new_size: int = None):
        if new_size is None:
            new_size = self.world_size + self._new_size_bias
        self._landscale = [self._landscale[x] + [0] * (new_size - self.world_size) for x in range(self.world_size)]
        self._landscale += [[0] * new_size for _ in range(new_size - self.world_size)]
        self.world_size = new_size
        self.init(self.seed)

    def get_chunk_biome(self, x, y) -> Biome | None:
        """Return none if no chunk found"""
        try:
            return Biomes.from_height(self._landscale[x][y])
        except IndexError:
            return


if __name__ == '__main__':
    ws = WorldService(2000, 10)
    ws.init()
    for _ in range(50):
        print('-' * 20)
        for y in range(ws.world_size):
            for x in range(ws.world_size):
                b = ws.get_chunk_biome(x, y)
                name = b.name if b is not None else 'plain'
                print(('.' if name == 'plain' else '!'), end='')
            print()
        ws.generate_new(ws.world_size + 1)
        input()

