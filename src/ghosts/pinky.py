from settings import PINK, DIRECTIONS
from src.ghost import Ghost, GhostMode


class Pinky(Ghost):
    """Pink ghost — targets 4 tiles ahead of Pacman."""
    scatter_target = (2, 0)
    color          = PINK
    dot_threshold  = 0   # exits house immediately

    def __init__(self, level, pacman, start_tile=(13, 14)):
        super().__init__(level, pacman, start_tile, start_mode=GhostMode.HOUSE)

    def _chase_target(self):
        px_t, py_t = self.pacman.tile
        dx, dy     = DIRECTIONS[self.pacman.direction]
        return (px_t + dx * 4, py_t + dy * 4)
