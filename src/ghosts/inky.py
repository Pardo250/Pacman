from settings import CYAN, DIRECTIONS
from src.ghost import Ghost, GhostMode


class Inky(Ghost):
    """Cyan ghost — flanks using a vector from Blinky through 2-tiles-ahead of Pacman."""
    scatter_target = (27, 30)
    color          = CYAN
    dot_threshold  = 30

    def __init__(self, level, pacman, blinky, start_tile=(11, 14)):
        self.blinky = blinky
        super().__init__(level, pacman, start_tile, start_mode=GhostMode.HOUSE)

    def _chase_target(self):
        px_t, py_t = self.pacman.tile
        dx, dy     = DIRECTIONS[self.pacman.direction]
        pivot_x    = px_t + dx * 2
        pivot_y    = py_t + dy * 2
        bx, by     = self.blinky.tile
        return (pivot_x * 2 - bx, pivot_y * 2 - by)
