"""
Synthesised sound effects — no external .wav files required.
All sounds are generated as WAV data in memory using Python stdlib only.
"""
import io
import math
import struct
import wave

import pygame


def _wav(freq, ms, vol=0.45, sr=22050, fade=80):
    """Sine tone WAV (mono 16-bit) returned as BytesIO."""
    n   = int(sr * ms / 1000)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        for i in range(n):
            t   = i / sr
            env = min(i, n - i, fade) / max(fade, 1)
            val = int(32767 * vol * env * math.sin(2 * math.pi * freq * t))
            w.writeframes(struct.pack("<h", val))
    buf.seek(0)
    return buf


def _sweep(f0, f1, ms, vol=0.45, sr=22050, fade=80):
    """Frequency sweep WAV (mono 16-bit)."""
    n   = int(sr * ms / 1000)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        phase = 0.0
        for i in range(n):
            env  = min(i, n - i, fade) / max(fade, 1)
            freq = f0 + (f1 - f0) * (i / n)
            phase += 2 * math.pi * freq / sr
            val  = int(32767 * vol * env * math.sin(phase))
            w.writeframes(struct.pack("<h", val))
    buf.seek(0)
    return buf


def _jingle(notes, ms_each, vol=0.4, sr=22050):
    """Simple ascending jingle from a list of frequencies."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        fade = int(sr * ms_each / 1000 * 0.15)
        for freq in notes:
            n = int(sr * ms_each / 1000)
            for i in range(n):
                t   = i / sr
                env = min(i, n - i, fade) / max(fade, 1)
                val = int(32767 * vol * env * math.sin(2 * math.pi * freq * t))
                w.writeframes(struct.pack("<h", val))
    buf.seek(0)
    return buf


class Sounds:
    def __init__(self):
        self._ok = False
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            self._chomp_a    = pygame.mixer.Sound(file=_wav(350, 55, 0.3))
            self._chomp_b    = pygame.mixer.Sound(file=_wav(270, 55, 0.3))
            self._power      = pygame.mixer.Sound(file=_wav(110, 260, 0.5))
            self._eat_ghost  = pygame.mixer.Sound(file=_sweep(350, 750, 160, 0.6))
            self._death      = pygame.mixer.Sound(file=_sweep(600, 40, 1000, 0.55))
            self._extra_life = pygame.mixer.Sound(file=_jingle([523, 659, 784, 1047], 120))
            self._fruit      = pygame.mixer.Sound(file=_sweep(500, 900, 200, 0.5))
            self._chomp_idx  = 0
            self._muted      = False
            self._ok         = True
        except Exception:
            pass   # game runs silently if audio init fails

    # ------------------------------------------------------------------
    def play_chomp(self):
        if not self._ok or self._muted:
            return
        s = self._chomp_a if self._chomp_idx % 2 == 0 else self._chomp_b
        s.stop()
        s.play()
        self._chomp_idx += 1

    def play_power(self):      self._play(self._power)
    def play_eat_ghost(self):  self._play(self._eat_ghost)
    def play_death(self):      self._play(self._death)
    def play_extra_life(self): self._play(self._extra_life)
    def play_fruit(self):      self._play(self._fruit)

    def toggle_mute(self):
        if self._ok:
            self._muted = not self._muted

    @property
    def muted(self):
        return not self._ok or self._muted

    def _play(self, snd):
        if self._ok and not self._muted:
            snd.play()
