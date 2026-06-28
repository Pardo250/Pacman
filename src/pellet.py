import pygame
from settings import MAP_COLS, MAP_ROWS, PELLET_CLR, POWER_CLR
from src.level import Tile
from src.utils import tile_center_pixel

_PELLET_R = 2
_POWER_R  = 4
_FLASH_HZ = 0.3   # seconds per flash cycle half


class PelletRenderer:
    def __init__(self, level):
        self.level = level
        self._timer = 0.0
        self._power_on = True

    def update(self, dt):
        self._timer += dt
        if self._timer >= _FLASH_HZ:
            self._timer -= _FLASH_HZ
            self._power_on = not self._power_on

    def draw(self, surface):
        for ty in range(MAP_ROWS):
            for tx in range(MAP_COLS):
                t = self.level.get_tile(tx, ty)
                if t == Tile.PELLET:
                    cx, cy = tile_center_pixel(tx, ty)
                    pygame.draw.circle(surface, PELLET_CLR, (cx, cy), _PELLET_R)
                elif t == Tile.POWER and self._power_on:
                    cx, cy = tile_center_pixel(tx, ty)
                    pygame.draw.circle(surface, POWER_CLR, (cx, cy), _POWER_R)
