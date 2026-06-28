import pygame
from settings import TILE_SIZE
from src.utils import tile_center_pixel

# (body_color, stem_color, score, name)
_FRUIT_TABLE = [
    ((210,  30,  30), (30, 130, 30),  100, "cherry"),
    ((220,  40,  60), (30, 130, 30),  300, "strawberry"),
    ((255, 140,   0), (30, 130, 30),  500, "orange"),
    ((200,   0,   0), (30, 130, 30),  700, "apple"),
    ((50,  200,  80), (30, 130, 30), 1000, "melon"),
    ((160,  32, 240), (30, 130, 30), 2000, "grapes"),
    ((255, 220,   0), (30, 130, 30), 3000, "bell"),
    ((255,  80,  80), (30, 130, 30), 5000, "key"),
]

_APPEAR_PELLETS = (70, 170)   # pellets eaten when fruit spawns
_DURATION       = 9.0          # seconds before fruit disappears
_TILE           = (13, 17)     # center of maze just below ghost house


class Fruit:
    def __init__(self, level_num):
        idx = min(level_num - 1, len(_FRUIT_TABLE) - 1)
        self.color, _, self.score, self.name = _FRUIT_TABLE[idx]
        self._timer  = _DURATION
        self.active  = True

        cx, cy = tile_center_pixel(*_TILE)
        self.px, self.py = float(cx), float(cy)

        r  = TILE_SIZE // 2 - 1
        sz = r * 2
        self.image = pygame.Surface((sz, sz), pygame.SRCALPHA)
        pygame.draw.circle(self.image, self.color, (r, r), r)
        # small shine dot
        pygame.draw.circle(self.image, (255, 255, 255), (r - r // 3, r - r // 3), max(r // 4, 1))
        self.rect = self.image.get_rect(center=(cx, cy))

    # ------------------------------------------------------------------
    def update(self, dt):
        if not self.active:
            return
        self._timer -= dt
        if self._timer <= 0:
            self.active = False

    def draw(self, surface):
        if self.active:
            surface.blit(self.image, self.rect)

    def check_eaten(self, pacman):
        if not self.active:
            return 0
        dist = ((pacman.px - self.px) ** 2 + (pacman.py - self.py) ** 2) ** 0.5
        if dist < TILE_SIZE:
            self.active = False
            return self.score
        return 0
