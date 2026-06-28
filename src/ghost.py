import math
import random
from enum import auto, Enum

import pygame

from settings import (
    TILE_SIZE, MAP_COLS, DIRECTIONS, OPPOSITE,
    GHOST_SPEED, GHOST_FRIGHT_SPEED, GHOST_EATEN_SPEED,
    GHOST_FRIGHT, GHOST_WHITE, WHITE, POWER_FLASH_TIME,
)
from src.level import Tile
from src.utils import pixel_to_tile, tile_center_pixel


class GhostMode(Enum):
    HOUSE      = auto()   # inside house, bobbing
    EXITING    = auto()   # navigating to exit tile
    SCATTER    = auto()
    CHASE      = auto()
    FRIGHTENED = auto()
    EATEN      = auto()   # eyes returning to house


_EXIT_TILE  = (13, 11)   # tile just above the ghost house door (outside)
_DOOR_TILE  = (13, 12)   # top row of ghost house (door tiles)

_HOUSE_TOP_ROW = 13   # row where ghost reverses UP→DOWN inside house
_HOUSE_BOT_ROW = 15   # row where ghost reverses DOWN→UP inside house


class Ghost(pygame.sprite.Sprite):
    # Override in subclasses
    scatter_target = (0, 0)
    color          = WHITE
    dot_threshold  = 0    # pellets eaten before this ghost exits HOUSE

    def __init__(self, level, pacman, start_tile, start_mode=GhostMode.HOUSE):
        super().__init__()
        self.level  = level
        self.pacman = pacman

        sz = TILE_SIZE
        self.image = pygame.Surface((sz, sz), pygame.SRCALPHA)
        self.rect  = self.image.get_rect()

        self.mode      = start_mode
        self.direction = "UP"

        self._fright_timer = 0.0
        self._fright_flash = False
        self.speed_mult    = 1.0   # set by Game per level

        tx, ty = start_tile
        cx, cy = tile_center_pixel(tx, ty)
        self.px = float(cx)
        self.py = float(cy)

        self._body_pts = _build_body_pts(sz)
        self._draw_sprite()
        self._sync_rect()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def frighten(self, duration):
        if self.mode not in (GhostMode.HOUSE, GhostMode.EXITING, GhostMode.EATEN):
            self.direction     = OPPOSITE[self.direction]
            self.mode          = GhostMode.FRIGHTENED
            self._fright_timer = duration
            self._fright_flash = False

    def eat(self):
        self.mode = GhostMode.EATEN

    def reset(self, start_tile, start_mode):
        tx, ty = start_tile
        cx, cy = tile_center_pixel(tx, ty)
        self.px, self.py   = float(cx), float(cy)
        self.mode          = start_mode
        self.direction     = "UP"
        self._fright_timer = 0.0
        self._fright_flash = False
        # speed_mult is NOT reset here — it persists across lives within a level
        self._draw_sprite()
        self._sync_rect()

    @property
    def tile(self):
        return pixel_to_tile(self.px, self.py)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt, global_mode):
        if self.mode == GhostMode.HOUSE:
            self._update_house(dt)
            return

        if self.mode == GhostMode.FRIGHTENED:
            self._fright_timer -= dt
            if self._fright_timer <= 0:
                self.mode = global_mode
            else:
                self._fright_flash = self._fright_timer <= POWER_FLASH_TIME

        elif self.mode not in (GhostMode.EXITING, GhostMode.EATEN):
            if global_mode != self.mode:
                self.direction = OPPOSITE[self.direction]
            self.mode = global_mode

        speed = self._speed() * dt
        self._move(speed)
        self._draw_sprite()
        self._sync_rect()

    # ------------------------------------------------------------------
    # Subclass hook
    # ------------------------------------------------------------------

    def _chase_target(self):
        return self.pacman.tile

    # ------------------------------------------------------------------
    # Movement
    # ------------------------------------------------------------------

    def _move(self, speed):
        tx, ty = pixel_to_tile(self.px, self.py)
        cx, cy = tile_center_pixel(tx, ty)

        dx, dy = DIRECTIONS[self.direction]

        # Keep the perpendicular axis snapped to the tile center
        if dx != 0:
            self.py = float(cy)
        else:
            self.px = float(cx)

        dist = abs(self.px - cx) if dx != 0 else abs(self.py - cy)

        if dist <= speed:
            self.px, self.py = float(cx), float(cy)

            # Arrival checks
            if self.mode == GhostMode.EXITING and (tx, ty) == _EXIT_TILE:
                self.mode = GhostMode.SCATTER   # will sync to global_mode next tick

            elif self.mode == GhostMode.EATEN and (tx, ty) == _DOOR_TILE:
                self.mode = GhostMode.EXITING   # re-enter play

            # Choose next direction
            if self.mode == GhostMode.FRIGHTENED:
                self.direction = self._random_dir(tx, ty)
            else:
                self.direction = self._greedy_dir(tx, ty)

        dx, dy = DIRECTIONS[self.direction]
        self.px += dx * speed
        self.py += dy * speed

        limit = MAP_COLS * TILE_SIZE
        if self.px < 0:
            self.px += limit
        elif self.px >= limit:
            self.px -= limit

    def _update_house(self, dt):
        speed = GHOST_SPEED * 0.5 * dt
        tx, ty = pixel_to_tile(self.px, self.py)
        cx, cy = tile_center_pixel(tx, ty)

        dist = abs(self.py - cy)
        if dist <= speed:
            self.py = float(cy)
            if self.direction == "UP" and ty <= _HOUSE_TOP_ROW:
                self.direction = "DOWN"
            elif self.direction == "DOWN" and ty >= _HOUSE_BOT_ROW:
                self.direction = "UP"

        self.px = float(cx)
        _, dy = DIRECTIONS[self.direction]
        self.py += dy * speed

        self._draw_sprite()
        self._sync_rect()

    # ------------------------------------------------------------------
    # Navigation helpers
    # ------------------------------------------------------------------

    def _target(self):
        if self.mode == GhostMode.SCATTER:  return self.scatter_target
        if self.mode == GhostMode.CHASE:    return self._chase_target()
        if self.mode == GhostMode.EXITING:  return _EXIT_TILE
        if self.mode == GhostMode.EATEN:    return _DOOR_TILE
        return self.scatter_target

    def _greedy_dir(self, tx, ty):
        target   = self._target()
        opp      = OPPOSITE[self.direction]
        best_dir = None
        best_d   = float('inf')

        # Original tiebreak order: UP > LEFT > DOWN > RIGHT
        for d in ("UP", "LEFT", "DOWN", "RIGHT"):
            if d == opp:
                continue
            dx, dy = DIRECTIONS[d]
            ntx, nty = tx + dx, ty + dy
            if not self._passable(ntx, nty):
                continue
            dist = math.hypot(ntx - target[0], nty - target[1])
            if dist < best_d:
                best_d   = dist
                best_dir = d

        return best_dir or opp  # fallback: reverse if completely boxed in

    def _random_dir(self, tx, ty):
        opp  = OPPOSITE[self.direction]
        opts = [
            d for d, (dx, dy) in DIRECTIONS.items()
            if d != opp and self._passable(tx + dx, ty + dy)
        ]
        return random.choice(opts) if opts else opp

    def _passable(self, tx, ty):
        t = self.level.get_tile(tx, ty)
        if t == Tile.WALL:
            return False
        if t == Tile.DOOR:
            # Ghosts only pass through the door when entering or exiting the house
            return self.mode in (GhostMode.EXITING, GhostMode.EATEN)
        return True

    def _speed(self):
        if self.mode == GhostMode.EATEN:      return GHOST_EATEN_SPEED
        if self.mode == GhostMode.FRIGHTENED: return GHOST_FRIGHT_SPEED * self.speed_mult
        return GHOST_SPEED * self.speed_mult

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def _draw_sprite(self):
        self.image.fill((0, 0, 0, 0))
        sz = self.image.get_width()

        if self.mode == GhostMode.EATEN:
            _draw_eyes(self.image, sz, self.direction, frightened=False)
            return

        if self.mode == GhostMode.FRIGHTENED:
            body_c = GHOST_WHITE if self._fright_flash else GHOST_FRIGHT
        else:
            body_c = self.color

        pygame.draw.polygon(self.image, body_c, self._body_pts)

        if self.mode == GhostMode.FRIGHTENED:
            _draw_frightened_face(self.image, sz)
        else:
            _draw_eyes(self.image, sz, self.direction, frightened=False)

    def _sync_rect(self):
        self.rect.center = (round(self.px), round(self.py))


# ------------------------------------------------------------------
# Sprite drawing helpers (module-level so they can be reused)
# ------------------------------------------------------------------

def _build_body_pts(sz):
    r  = sz / 2 - 1
    cx = sz / 2
    cy = r  # y-center of the top semicircle
    pts = []

    # Top semicircle: left → right (angles π → 0)
    for i in range(13):
        a = math.pi * (1 - i / 12)
        pts.append((cx + r * math.cos(a), cy - r * math.sin(a)))

    # Scalloped skirt: 3 bumps going right → left
    bump_h = max(sz // 5, 2)
    w3 = sz / 3
    for i in range(3):
        xi = 2 - i
        x0 = xi * w3
        x1 = x0 + w3
        xm = (x0 + x1) / 2
        pts.append((x1 - 1, sz - bump_h))
        pts.append((xm,     sz - 1))
        pts.append((x0,     sz - bump_h))

    return pts


def _draw_eyes(surf, sz, direction, frightened):
    er = max(sz // 5, 2)
    lx = sz // 3
    rx = sz * 2 // 3
    ey = sz * 2 // 5

    pygame.draw.circle(surf, WHITE, (lx, ey), er)
    pygame.draw.circle(surf, WHITE, (rx, ey), er)

    if not frightened:
        off = {"RIGHT": (er // 2, 0), "LEFT": (-er // 2, 0),
               "UP": (0, -er // 2),   "DOWN": (0,  er // 2)}
        ox, oy = off.get(direction, (0, 0))
        pr = max(er // 2, 1)
        pygame.draw.circle(surf, (33, 33, 255), (lx + ox, ey + oy), pr)
        pygame.draw.circle(surf, (33, 33, 255), (rx + ox, ey + oy), pr)


def _draw_frightened_face(surf, sz):
    ey = sz * 2 // 5
    er = max(sz // 7, 1)
    pygame.draw.circle(surf, WHITE, (sz // 3,     ey), er)
    pygame.draw.circle(surf, WHITE, (sz * 2 // 3, ey), er)

    ym   = sz * 3 // 5
    segs = 4
    pts  = [
        (sz * i // segs, ym + (sz // 12 if i % 2 == 0 else -sz // 12))
        for i in range(segs + 1)
    ]
    if len(pts) > 1:
        pygame.draw.lines(surf, WHITE, False, pts, 1)
