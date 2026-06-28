from settings import TILE_SIZE


def tile_to_pixel(tx, ty):
    return tx * TILE_SIZE, ty * TILE_SIZE


def pixel_to_tile(px, py):
    return int(px // TILE_SIZE), int(py // TILE_SIZE)


def tile_center_pixel(tx, ty):
    half = TILE_SIZE // 2
    return tx * TILE_SIZE + half, ty * TILE_SIZE + half
