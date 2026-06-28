import math

from settings import ORANGE
from src.ghost import Ghost, GhostMode


class Clyde(Ghost):
    """Orange ghost — chases like Blinky when far, flees to corner when close."""
    scatter_target = (0, 30)
    color          = ORANGE
    dot_threshold  = 60

    def __init__(self, level, pacman, start_tile=(15, 14)):
        super().__init__(level, pacman, start_tile, start_mode=GhostMode.HOUSE)

    def _chase_target(self):
        tx, ty     = self.tile
        px_t, py_t = self.pacman.tile
        dist       = math.hypot(tx - px_t, ty - py_t)
        if dist > 8:
            return (px_t, py_t)
        return self.scatter_target
