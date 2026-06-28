import pygame
from settings import SCALE, YELLOW

_DURATION  = 0.8    # seconds visible
_RISE_SPEED = 18    # native pixels per second (upward)


class ScorePopup:
    def __init__(self, font, value, native_x, native_y):
        self.surf   = font.render(str(value), True, YELLOW)
        self._nx    = float(native_x)
        self._ny    = float(native_y)
        self._timer = _DURATION
        self.dead   = False

    def update(self, dt):
        self._ny    -= _RISE_SPEED * dt
        self._timer -= dt
        if self._timer <= 0:
            self.dead = True

    def draw(self, screen):
        if not self.dead:
            r = self.surf.get_rect(center=(round(self._nx * SCALE),
                                           round(self._ny * SCALE)))
            screen.blit(self.surf, r)
