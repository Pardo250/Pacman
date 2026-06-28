class CollisionSystem:
    def check_pellet(self, pacman, level):
        tx, ty = pacman.tile
        return level.consume(tx, ty)
