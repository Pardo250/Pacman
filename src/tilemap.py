import pygame
from settings import TILE_SIZE, MAP_COLS, MAP_ROWS, WALL_BLUE, WALL_DARK, BLACK
from src.level import Tile

_EDGE = 2   # bright-edge width in pixels


class TileMap:
    def __init__(self, level):
        self.level = level
        w = MAP_COLS * TILE_SIZE
        h = MAP_ROWS * TILE_SIZE
        self.surface = pygame.Surface((w, h))
        self._render()

    def _render(self):
        self.surface.fill(BLACK)
        for ty in range(MAP_ROWS):
            for tx in range(MAP_COLS):
                t = self.level.get_tile(tx, ty)
                x, y = tx * TILE_SIZE, ty * TILE_SIZE

                if t == Tile.WALL:
                    # Dark fill
                    pygame.draw.rect(self.surface, WALL_DARK,
                                     (x, y, TILE_SIZE, TILE_SIZE))
                    # Bright edges facing open space
                    if not self.level.is_wall(tx, ty - 1):
                        pygame.draw.rect(self.surface, WALL_BLUE,
                                         (x, y, TILE_SIZE, _EDGE))
                    if not self.level.is_wall(tx, ty + 1):
                        pygame.draw.rect(self.surface, WALL_BLUE,
                                         (x, y + TILE_SIZE - _EDGE, TILE_SIZE, _EDGE))
                    if not self.level.is_wall(tx - 1, ty):
                        pygame.draw.rect(self.surface, WALL_BLUE,
                                         (x, y, _EDGE, TILE_SIZE))
                    if not self.level.is_wall(tx + 1, ty):
                        pygame.draw.rect(self.surface, WALL_BLUE,
                                         (x + TILE_SIZE - _EDGE, y, _EDGE, TILE_SIZE))

                elif t == Tile.DOOR:
                    mid = y + TILE_SIZE // 2
                    pygame.draw.rect(self.surface, (255, 182, 255),
                                     (x, mid - 1, TILE_SIZE, 2))

    def draw(self, surface):
        surface.blit(self.surface, (0, 0))
