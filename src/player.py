import math
import pygame
from settings import TILE_SIZE, MAP_COLS, YELLOW, DIRECTIONS, PACMAN_SPEED
from src.utils import pixel_to_tile, tile_center_pixel
from src.level import Tile


class Pacman(pygame.sprite.Sprite):
    def __init__(self, level, start_tile):
        super().__init__()
        self.level = level
        self.start_tile = start_tile

        sz = TILE_SIZE - 2
        self.image = pygame.Surface((sz, sz), pygame.SRCALPHA)
        self.rect  = self.image.get_rect()

        self.direction    = "LEFT"
        self.buffered_dir = "LEFT"

        tx, ty = start_tile
        cx, cy = tile_center_pixel(tx, ty)
        self.px = float(cx)
        self.py = float(cy)

        self._anim_t   = 0.0
        self._mouth    = 0   # current mouth angle in degrees
        self._draw_sprite()
        self._sync_rect()

    # ------------------------------------------------------------------
    def handle_input(self, keys):
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: self.buffered_dir = "LEFT"
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.buffered_dir = "RIGHT"
        if keys[pygame.K_UP]    or keys[pygame.K_w]: self.buffered_dir = "UP"
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: self.buffered_dir = "DOWN"

    def update(self, dt):
        speed = PACMAN_SPEED * dt

        tx, ty = pixel_to_tile(self.px, self.py)
        cx, cy = tile_center_pixel(tx, ty)

        dx, dy = DIRECTIONS[self.direction]

        # Keep perpendicular axis locked to tile center (prevents drift)
        if dx != 0:
            self.py = float(cy)
        else:
            self.px = float(cx)

        # Distance to current tile center along movement axis
        dist = abs(self.px - cx) if dx != 0 else abs(self.py - cy)

        if dist <= speed:
            # Snap to center, evaluate direction change
            self.px, self.py = float(cx), float(cy)

            bdx, bdy = DIRECTIONS[self.buffered_dir]
            if self.level.is_passable(tx + bdx, ty + bdy):
                self.direction = self.buffered_dir
                dx, dy = DIRECTIONS[self.direction]

            if not self.level.is_passable(tx + dx, ty + dy):
                self._animate(dt)
                self._sync_rect()
                return

        dx, dy = DIRECTIONS[self.direction]
        self.px += dx * speed
        self.py += dy * speed

        # Tunnel wrap
        limit = MAP_COLS * TILE_SIZE
        if self.px < 0:
            self.px += limit
        elif self.px >= limit:
            self.px -= limit

        self._animate(dt)
        self._sync_rect()

    # ------------------------------------------------------------------
    def reset(self):
        tx, ty = self.start_tile
        cx, cy = tile_center_pixel(tx, ty)
        self.px, self.py = float(cx), float(cy)
        self.direction    = "LEFT"
        self.buffered_dir = "LEFT"
        self._sync_rect()

    @property
    def tile(self):
        return pixel_to_tile(self.px, self.py)

    # ------------------------------------------------------------------
    def _sync_rect(self):
        self.rect.center = (round(self.px), round(self.py))

    def _animate(self, dt):
        self._anim_t = (self._anim_t + dt * 8) % 1.0
        phase = abs(self._anim_t - 0.5) * 2   # 0→1→0
        self._mouth = int(phase * 45)
        self._draw_sprite()

    def _draw_sprite(self):
        self.image.fill((0, 0, 0, 0))
        sz  = self.image.get_width()
        cx_ = cy_ = sz // 2
        r   = sz // 2

        if self._mouth == 0:
            pygame.draw.circle(self.image, YELLOW, (cx_, cy_), r)
            return

        # Map direction to base angle (standard math CCW, y-flipped for screen)
        base = {"RIGHT": 0, "LEFT": 180, "UP": 90, "DOWN": 270}[self.direction]
        start = base + self._mouth
        end   = base + 360 - self._mouth

        points = [(cx_, cy_)]
        steps  = 32
        for i in range(steps + 1):
            a = math.radians(start + (end - start) * i / steps)
            points.append((cx_ + r * math.cos(a), cy_ - r * math.sin(a)))

        pygame.draw.polygon(self.image, YELLOW, points)
