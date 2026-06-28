from src.ghost import GhostMode

# Sequence: (mode, duration_in_seconds). -1 = infinite.
_SEQUENCE = [
    (GhostMode.SCATTER,  7.0),
    (GhostMode.CHASE,   20.0),
    (GhostMode.SCATTER,  7.0),
    (GhostMode.CHASE,   20.0),
    (GhostMode.SCATTER,  5.0),
    (GhostMode.CHASE,   20.0),
    (GhostMode.SCATTER,  5.0),
    (GhostMode.CHASE,   -1.0),   # permanent chase
]


class ModeController:
    def __init__(self):
        self._idx   = 0
        self._timer = 0.0
        self.mode   = GhostMode.SCATTER

    def update(self, dt):
        _, duration = _SEQUENCE[self._idx]
        if duration < 0:
            return
        self._timer += dt
        if self._timer >= duration:
            self._timer -= duration
            self._idx  = min(self._idx + 1, len(_SEQUENCE) - 1)
            self.mode, _ = _SEQUENCE[self._idx]

    def reset(self):
        self._idx   = 0
        self._timer = 0.0
        self.mode   = GhostMode.SCATTER
