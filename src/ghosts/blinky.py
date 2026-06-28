from settings import RED
from src.ghost import Ghost, GhostMode


class Blinky(Ghost):
    """Red ghost — chases Pacman directly. Starts outside the house."""
    scatter_target = (25, 0)
    color          = RED
    dot_threshold  = -1   # never enters HOUSE; starts in SCATTER

    def __init__(self, level, pacman, start_tile=(13, 11)):
        super().__init__(level, pacman, start_tile, start_mode=GhostMode.SCATTER)
        self.direction = "RIGHT"   # initial heading toward scatter corner

    def _chase_target(self):
        return self.pacman.tile
