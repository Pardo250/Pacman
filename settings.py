import pygame

# Tile dimensions
TILE_SIZE = 16          # pixels per tile at native resolution
SCALE     = 2           # render scale multiplier
MAP_COLS  = 28
MAP_ROWS  = 36

# Window
WIN_W = MAP_COLS * TILE_SIZE * SCALE   # 896
WIN_H = MAP_ROWS * TILE_SIZE * SCALE   # 1152
FPS   = 60

# Speeds (pixels per second at native resolution)
PACMAN_SPEED      = 80.0
GHOST_SPEED       = 70.0
GHOST_FRIGHT_SPEED = 35.0
GHOST_EATEN_SPEED  = 120.0

# Scoring
PELLET_SCORE     = 10
POWER_SCORE      = 50
GHOST_SCORES     = [200, 400, 800, 1600]
EXTRA_LIFE_SCORE = 10_000

# Ghost timers (seconds)
POWER_DURATION   = 6.0
POWER_FLASH_TIME = 2.0   # seconds before power ends when ghosts start flashing

# Ghost dot counters for leaving house
GHOST_DOT_LIMITS = {
    "pinky": 0,
    "inky":  30,
    "clyde": 60,
}

# Colors
BLACK       = (0,   0,   0)
WHITE       = (255, 255, 255)
YELLOW      = (255, 255, 0)
BLUE        = (33,  33,  255)
WALL_BLUE   = (33,  33,  255)
WALL_DARK   = (0,   0,   150)
PELLET_CLR  = (255, 185, 131)
POWER_CLR   = (255, 185, 131)
RED         = (255, 0,   0)
PINK        = (255, 184, 255)
CYAN        = (0,   255, 255)
ORANGE      = (255, 184, 82)
GHOST_FRIGHT = (33, 33,  255)
GHOST_WHITE  = (255, 255, 255)
TEXT_CLR    = (255, 255, 255)
SCORE_CLR   = (255, 255, 255)

# Direction vectors (dx, dy) in tile space
DIRECTIONS = {
    "LEFT":  (-1,  0),
    "RIGHT": ( 1,  0),
    "UP":    ( 0, -1),
    "DOWN":  ( 0,  1),
}

OPPOSITE = {
    "LEFT":  "RIGHT",
    "RIGHT": "LEFT",
    "UP":    "DOWN",
    "DOWN":  "UP",
}
