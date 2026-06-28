from enum import IntEnum
from settings import MAP_COLS, MAP_ROWS, PELLET_SCORE, POWER_SCORE


class Tile(IntEnum):
    EMPTY  = 0
    WALL   = 1
    PELLET = 2
    POWER  = 3
    DOOR   = 4


_CHAR_MAP = {
    '#': Tile.WALL,
    '.': Tile.PELLET,
    'o': Tile.POWER,
    '-': Tile.DOOR,
    ' ': Tile.EMPTY,
}


class Level:
    def __init__(self, path):
        self.grid = []
        self.pellet_count = 0
        self._load(path)

    def _load(self, path):
        with open(path, 'r') as f:
            lines = f.read().splitlines()

        for row_idx in range(MAP_ROWS):
            raw = lines[row_idx] if row_idx < len(lines) else ''
            # Pad or trim to exactly MAP_COLS characters
            raw = raw.ljust(MAP_COLS)[:MAP_COLS]
            row = []
            for ch in raw:
                tile = _CHAR_MAP.get(ch, Tile.EMPTY)
                if tile in (Tile.PELLET, Tile.POWER):
                    self.pellet_count += 1
                row.append(tile)
            self.grid.append(row)

    def get_tile(self, tx, ty):
        if 0 <= ty < MAP_ROWS and 0 <= tx < MAP_COLS:
            return self.grid[ty][tx]
        return Tile.WALL

    def is_wall(self, tx, ty):
        return self.get_tile(tx, ty) == Tile.WALL

    def is_passable(self, tx, ty):
        return self.get_tile(tx, ty) not in (Tile.WALL, Tile.DOOR)

    def consume(self, tx, ty):
        """Remove pellet at (tx, ty) and return its score value."""
        t = self.get_tile(tx, ty)
        if t == Tile.PELLET:
            self.grid[ty][tx] = Tile.EMPTY
            self.pellet_count -= 1
            return PELLET_SCORE
        if t == Tile.POWER:
            self.grid[ty][tx] = Tile.EMPTY
            self.pellet_count -= 1
            return POWER_SCORE
        return 0
