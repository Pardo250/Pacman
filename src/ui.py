import pygame
from settings import SCALE, TILE_SIZE, MAP_COLS, MAP_ROWS, YELLOW, WHITE


class HUD:
    def __init__(self):
        self.font       = pygame.font.SysFont("monospace", 14 * SCALE, bold=True)
        self.small_font = pygame.font.SysFont("monospace", 10 * SCALE, bold=True)

    def draw(self, surface, score, lives, level_num):
        # Score — top-left corner
        txt = self.font.render(f"SCORE  {score:06d}", True, WHITE)
        surface.blit(txt, (8 * SCALE, 4 * SCALE))

        # Lives — bottom-left as small Pacman icons
        life_r = (TILE_SIZE * SCALE) // 2 - 2
        base_x = 16 * SCALE
        base_y = (MAP_ROWS - 1) * TILE_SIZE * SCALE + TILE_SIZE * SCALE // 2
        for i in range(lives):
            pygame.draw.circle(surface, YELLOW, (base_x + i * (life_r * 2 + 4), base_y), life_r)

        # Level number — bottom-right
        lvl = self.small_font.render(f"LVL {level_num}", True, WHITE)
        surface.blit(lvl, (MAP_COLS * TILE_SIZE * SCALE - lvl.get_width() - 8 * SCALE,
                           (MAP_ROWS - 1) * TILE_SIZE * SCALE + 4 * SCALE))
