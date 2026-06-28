import sys
from enum import auto, Enum

import pygame

from settings import (
    WIN_W, WIN_H, FPS, MAP_COLS, MAP_ROWS, TILE_SIZE, SCALE,
    BLACK, WHITE, YELLOW, RED, PINK, CYAN, ORANGE,
    GHOST_SCORES, EXTRA_LIFE_SCORE, POWER_DURATION,
    WALL_BLUE, WALL_DARK,
)
from src.level import Level
from src.tilemap import TileMap
from src.player import Pacman
from src.pellet import PelletRenderer
from src.collision import CollisionSystem
from src.ui import HUD
from src.ghost import GhostMode
from src.mode_controller import ModeController
from src.ghosts.blinky import Blinky
from src.ghosts.pinky import Pinky
from src.ghosts.inky import Inky
from src.ghosts.clyde import Clyde
from src.fruit import Fruit, _APPEAR_PELLETS
from src.score_popup import ScorePopup
from src.sounds import Sounds
from src import highscore


_PACMAN_START = (13, 23)
_BLINKY_START = (13, 11)
_PINKY_START  = (13, 14)
_INKY_START   = (11, 14)
_CLYDE_START  = (15, 14)

_HIT_RADIUS   = 6     # pixel radius for ghost–Pacman collision


class _State(Enum):
    MENU        = auto()
    READY       = auto()   # "READY!" for 1.5 s before play
    PLAYING     = auto()
    PAUSED      = auto()
    DYING       = auto()   # 2 s freeze after Pacman death
    LEVEL_CLEAR = auto()   # maze flash when all pellets eaten
    GAME_OVER   = auto()


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Pac-Man")
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        self.clock  = pygame.time.Clock()
        self.canvas = pygame.Surface((MAP_COLS * TILE_SIZE, MAP_ROWS * TILE_SIZE))

        self.sounds  = Sounds()
        self.hud     = HUD()
        self.collision = CollisionSystem()
        self._high   = highscore.load()

        # Fonts (drawn on screen-space, already scaled)
        self._font_big   = pygame.font.SysFont("monospace", 22 * SCALE, bold=True)
        self._font_med   = pygame.font.SysFont("monospace", 14 * SCALE, bold=True)
        self._font_small = pygame.font.SysFont("monospace",  9 * SCALE, bold=True)
        self._font_popup = pygame.font.SysFont("monospace", 10 * SCALE, bold=True)

        self._menu_blink = 0.0   # blink timer for menu "PRESS SPACE"
        self._menu_show  = True

        self.score     = 0
        self.lives     = 3
        self.level_num = 1
        self._state    = _State.MENU

        # These are created properly in _load_level()
        self.level = self.tilemap = self.player = self.pellets = None
        self.blinky = self.pinky = self.inky = self.clyde = None
        self.ghosts = []

        self._popups: list[ScorePopup] = []
        self._fruit: Fruit | None = None
        self._fruit_idx  = 0   # which fruit appearance (0 or 1 per level)

    # ==================================================================
    # Run loop
    # ==================================================================

    def run(self):
        while True:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            self._handle_events()
            self._update(dt)
            self._draw()

    # ==================================================================
    # Event handling
    # ==================================================================

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._quit()
            if event.type == pygame.KEYDOWN:
                self._on_key(event.key)

        if self._state == _State.PLAYING:
            self.player.handle_input(pygame.key.get_pressed())

    def _on_key(self, key):
        if key == pygame.K_ESCAPE:
            self._quit()

        if key == pygame.K_m:
            self.sounds.toggle_mute()

        if self._state == _State.MENU:
            if key == pygame.K_SPACE:
                self._new_game()

        elif self._state == _State.PLAYING:
            if key == pygame.K_p:
                self._state = _State.PAUSED

        elif self._state == _State.PAUSED:
            if key == pygame.K_p:
                self._state = _State.PLAYING

        elif self._state == _State.GAME_OVER:
            if key == pygame.K_RETURN:
                self._state = _State.MENU

    # ==================================================================
    # Update
    # ==================================================================

    def _update(self, dt):
        s = self._state
        if s == _State.MENU:
            self._update_menu(dt)
        elif s == _State.READY:
            self._update_ready(dt)
        elif s == _State.PLAYING:
            self._update_playing(dt)
        elif s == _State.DYING:
            self._update_dying(dt)
        elif s == _State.LEVEL_CLEAR:
            self._update_level_clear(dt)
        # PAUSED / GAME_OVER / MENU: nothing moves

        # Popups always update when visible
        for p in self._popups:
            p.update(dt)
        self._popups = [p for p in self._popups if not p.dead]

    # ----- state sub-updates ------------------------------------------

    def _update_menu(self, dt):
        self._menu_blink += dt
        if self._menu_blink >= 0.5:
            self._menu_blink  = 0.0
            self._menu_show   = not self._menu_show

    def _update_ready(self, dt):
        self._ready_timer -= dt
        if self._ready_timer <= 0:
            self._state = _State.PLAYING

    def _update_playing(self, dt):
        global_mode = self.mode_ctrl.mode
        self.mode_ctrl.update(dt)

        self.player.update(dt)
        self.pellets.update(dt)

        # Fruit
        if self._fruit:
            self._fruit.update(dt)
            pts = self._fruit.check_eaten(self.player)
            if pts:
                self.score += pts
                self.sounds.play_fruit()
                self._add_popup(pts, self._fruit.px, self._fruit.py)

        # Pellet eating
        gained = self.collision.check_pellet(self.player, self.level)
        if gained:
            self._pellets_eaten += 1
            self.score += gained

            if gained == 50:                  # power pellet
                self._ghost_chain = 0
                fright_dur = max(POWER_DURATION - (self.level_num - 1) * 1.0, 2.0)
                for g in self.ghosts:
                    g.frighten(fright_dur)
                self.sounds.play_power()
            else:
                self.sounds.play_chomp()

            if self.score >= EXTRA_LIFE_SCORE and self.lives < 5:
                self.lives += 1
                self.sounds.play_extra_life()

            self._check_high()
            self._check_house_releases()
            self._check_fruit_spawn()

        # Level cleared
        if self.level.pellet_count == 0:
            self._state       = _State.LEVEL_CLEAR
            self._clear_timer = 2.2
            self._clear_phase = 0.0
            return

        # Ghosts
        for g in self.ghosts:
            g.update(dt, global_mode)

        # Ghost–Pacman collision
        self._check_ghost_collisions()

    def _update_dying(self, dt):
        self._death_timer -= dt
        if self._death_timer <= 0:
            self.lives -= 1
            if self.lives <= 0:
                self._check_high()
                highscore.save(self._high)
                self._state = _State.GAME_OVER
            else:
                self._reset_positions()
                self._enter_ready()

    def _update_level_clear(self, dt):
        self._clear_timer -= dt
        self._clear_phase += dt
        if self._clear_timer <= 0:
            self.level_num += 1
            self._load_level()
            self._enter_ready()

    # ----- helpers ----------------------------------------------------

    def _check_house_releases(self):
        for g in self.ghosts:
            if g.mode == GhostMode.HOUSE and g.dot_threshold >= 0:
                if self._pellets_eaten >= g.dot_threshold:
                    g.mode = GhostMode.EXITING

    def _check_ghost_collisions(self):
        px, py = self.player.px, self.player.py
        for g in self.ghosts:
            if g.mode in (GhostMode.HOUSE, GhostMode.EXITING, GhostMode.EATEN):
                continue
            dist = ((g.px - px) ** 2 + (g.py - py) ** 2) ** 0.5
            if dist > _HIT_RADIUS:
                continue
            if g.mode == GhostMode.FRIGHTENED:
                g.eat()
                pts = GHOST_SCORES[min(self._ghost_chain, len(GHOST_SCORES) - 1)]
                self.score       += pts
                self._ghost_chain += 1
                self._check_high()
                self.sounds.play_eat_ghost()
                self._add_popup(pts, g.px, g.py)
            else:
                self._state       = _State.DYING
                self._death_timer = 2.0
                self.sounds.play_death()
                return

    def _check_fruit_spawn(self):
        if self._fruit_idx < len(_APPEAR_PELLETS):
            if self._pellets_eaten >= _APPEAR_PELLETS[self._fruit_idx]:
                self._fruit      = Fruit(self.level_num)
                self._fruit_idx += 1

    def _check_high(self):
        if self.score > self._high:
            self._high = self.score

    def _add_popup(self, value, nx, ny):
        self._popups.append(ScorePopup(self._font_popup, value, nx, ny))

    # ==================================================================
    # Game lifecycle
    # ==================================================================

    def _new_game(self):
        self.score     = 0
        self.lives     = 3
        self.level_num = 1
        self._load_level()
        self._enter_ready()

    def _enter_ready(self):
        self._state       = _State.READY
        self._ready_timer = 1.5

    def _load_level(self):
        self.level   = Level("maps/level1.txt")
        self.tilemap = TileMap(self.level)
        self.player  = Pacman(self.level, _PACMAN_START)
        self.pellets = PelletRenderer(self.level)
        self.mode_ctrl = ModeController()

        self.blinky = Blinky(self.level, self.player)
        self.pinky  = Pinky(self.level, self.player)
        self.inky   = Inky(self.level, self.player, self.blinky)
        self.clyde  = Clyde(self.level, self.player)
        self.ghosts = [self.blinky, self.pinky, self.inky, self.clyde]

        # Speed increases every level (capped at 1.5×)
        mult = min(1.0 + (self.level_num - 1) * 0.1, 1.5)
        for g in self.ghosts:
            g.speed_mult = mult

        self._popups        = []
        self._fruit         = None
        self._fruit_idx     = 0
        self._death_timer   = 0.0
        self._ghost_chain   = 0
        self._pellets_eaten = 0

    def _reset_positions(self):
        self.player.reset()
        self.blinky.reset(_BLINKY_START, GhostMode.SCATTER)
        self.blinky.direction = "RIGHT"
        self.pinky.reset(_PINKY_START, GhostMode.HOUSE)
        self.inky.reset(_INKY_START,   GhostMode.HOUSE)
        self.clyde.reset(_CLYDE_START, GhostMode.HOUSE)
        self.mode_ctrl.reset()
        self._ghost_chain = 0
        self._popups.clear()

    @staticmethod
    def _quit():
        pygame.quit()
        sys.exit()

    # ==================================================================
    # Drawing
    # ==================================================================

    def _draw(self):
        s = self._state
        if s == _State.MENU:
            self._draw_menu()
        else:
            self._draw_game()
            if s == _State.READY:
                self._draw_centered("READY!", YELLOW)
            elif s == _State.PAUSED:
                self._draw_centered("PAUSED", WHITE)
            elif s == _State.LEVEL_CLEAR:
                self._draw_level_clear_flash()
            elif s == _State.GAME_OVER:
                self._draw_centered("GAME OVER", RED,
                                    sub="ENTER para volver al menu")

        # Popups always on top
        for p in self._popups:
            p.draw(self.screen)

        pygame.display.flip()

    # ----- menu -------------------------------------------------------

    def _draw_menu(self):
        self.screen.fill(BLACK)
        cx = WIN_W // 2

        # Title
        title = self._font_big.render("PAC-MAN", True, YELLOW)
        self.screen.blit(title, title.get_rect(center=(cx, WIN_H // 5)))

        # High score
        hi_lbl = self._font_med.render(f"HI-SCORE  {self._high:06d}", True, WHITE)
        self.screen.blit(hi_lbl, hi_lbl.get_rect(center=(cx, WIN_H // 5 + 60 * SCALE)))

        # Ghost showcase
        ghost_colors = [RED, PINK, CYAN, ORANGE]
        ghost_names  = ["BLINKY", "PINKY", "INKY", "CLYDE"]
        row_y = WIN_H // 2 - 20 * SCALE
        total_w = len(ghost_colors) * 64 * SCALE
        start_x = (WIN_W - total_w) // 2
        for i, (c, name) in enumerate(zip(ghost_colors, ghost_names)):
            gx = start_x + i * 64 * SCALE + 20 * SCALE
            pygame.draw.circle(self.screen, c, (gx, row_y), 12 * SCALE)
            lbl = self._font_small.render(name, True, c)
            self.screen.blit(lbl, lbl.get_rect(center=(gx, row_y + 18 * SCALE)))

        # Controls
        lines = [
            "CONTROLES: WASD / FLECHAS",
            "P = PAUSA    M = SILENCIO",
        ]
        for i, line in enumerate(lines):
            s = self._font_small.render(line, True, (180, 180, 180))
            self.screen.blit(s, s.get_rect(center=(cx, WIN_H * 2 // 3 + i * 22 * SCALE)))

        # Blinking "PRESS SPACE"
        if self._menu_show:
            sp = self._font_med.render("PRESIONA SPACE PARA JUGAR", True, YELLOW)
            self.screen.blit(sp, sp.get_rect(center=(cx, WIN_H * 4 // 5)))

        # Mute indicator
        if self.sounds.muted:
            m = self._font_small.render("SONIDO: OFF", True, (150, 150, 150))
            self.screen.blit(m, (8 * SCALE, WIN_H - 20 * SCALE))

    # ----- in-game ----------------------------------------------------

    def _draw_game(self):
        self.canvas.fill(BLACK)

        if self._state == _State.LEVEL_CLEAR:
            # Flash walls instead of normal maze
            flash_on = int(self._clear_phase / 0.35) % 2 == 0
            self._draw_flash_maze(flash_on)
        else:
            self.tilemap.draw(self.canvas)
            self.pellets.draw(self.canvas)

            if self._fruit:
                self._fruit.draw(self.canvas)

            for g in self.ghosts:
                self.canvas.blit(g.image, g.rect)

            self.canvas.blit(self.player.image, self.player.rect)

        scaled = pygame.transform.scale(self.canvas, (WIN_W, WIN_H))
        self.screen.blit(scaled, (0, 0))
        self.hud.draw(self.screen, self.score, self.lives, self.level_num)

        # HI-SCORE top-center
        hi = self._font_small.render(f"HI {self._high:06d}", True, WHITE)
        self.screen.blit(hi, hi.get_rect(center=(WIN_W // 2, 4 * SCALE)))

        # Mute indicator
        if self.sounds.muted:
            m = self._font_small.render("MUTE", True, (120, 120, 120))
            self.screen.blit(m, (WIN_W - m.get_width() - 6 * SCALE, 4 * SCALE))

    def _draw_flash_maze(self, flash_on):
        color = WALL_BLUE if flash_on else WHITE
        for ty in range(MAP_ROWS):
            for tx in range(MAP_COLS):
                from src.level import Tile
                t = self.level.get_tile(tx, ty)
                if t == Tile.WALL:
                    x, y = tx * TILE_SIZE, ty * TILE_SIZE
                    pygame.draw.rect(self.canvas, color,
                                     (x, y, TILE_SIZE, TILE_SIZE))

    def _draw_centered(self, text, color, sub=None):
        cx, cy = WIN_W // 2, WIN_H // 2
        surf = self._font_big.render(text, True, color)
        self.screen.blit(surf, surf.get_rect(center=(cx, cy)))
        if sub:
            s2 = self._font_small.render(sub, True, WHITE)
            self.screen.blit(s2, s2.get_rect(center=(cx, cy + 36 * SCALE)))

    def _draw_level_clear_flash(self):
        # Nothing extra — the flashing canvas is drawn in _draw_game()
        pass
