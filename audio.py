"""Procedural audio synthesis for win/loss sound effects."""

from __future__ import annotations

import math
import struct
import pygame


def generate_fanfare_sound(sample_rate: int = 44100) -> pygame.mixer.Sound | None:
    """Generate a celebratory fanfare sound effect."""
    try:
        # Fanfare notes: C5 (523.25), E5 (659.25), G5 (783.99), C6 (1046.50)
        notes = [
            (523.25, 0.10, 0.4),
            (659.25, 0.10, 0.4),
            (783.99, 0.10, 0.4),
            (1046.50, 0.35, 0.5),
        ]
        samples: list[int] = []
        for freq, duration, volume in notes:
            n_samples = int(sample_rate * duration)
            for i in range(n_samples):
                t = i / sample_rate
                progress = i / n_samples
                env = 1.0 - progress
                val_float = (
                    math.sin(2 * math.pi * freq * t) * 0.7
                    + math.sin(2 * math.pi * freq * 2 * t) * 0.3
                ) * env * volume
                val = max(-32768, min(32767, int(32767 * val_float)))
                samples.append(val)

        buf = struct.pack("<" + "h" * len(samples), *samples)
        return pygame.mixer.Sound(buffer=buf)
    except Exception:
        return None


def generate_womp_womp_sound(sample_rate: int = 44100) -> pygame.mixer.Sound | None:
    """Generate a 'womp womp' sad trombone loss sound effect."""
    try:
        # Sad trombone sequence: Eb4 (311.13), D4 (293.66), Db4 (277.18), C4 pitch sliding down (261.63 -> 200.00)
        notes = [
            (311.13, 311.13, 0.22, 0.4),
            (293.66, 293.66, 0.22, 0.4),
            (277.18, 277.18, 0.22, 0.4),
            (261.63, 200.00, 0.55, 0.5),
        ]
        samples: list[int] = []
        for start_freq, end_freq, duration, volume in notes:
            n_samples = int(sample_rate * duration)
            phase = 0.0
            for i in range(n_samples):
                progress = i / n_samples
                freq = start_freq + (end_freq - start_freq) * progress
                phase += 2 * math.pi * freq / sample_rate

                val_float = (
                    math.sin(phase) * 0.5
                    + math.sin(phase * 2) * 0.25
                    + math.sin(phase * 3) * 0.125
                )

                env = (i / (n_samples * 0.1)) if progress < 0.1 else (1.0 - progress)
                val_float *= env * volume
                val = max(-32768, min(32767, int(32767 * val_float)))
                samples.append(val)

        buf = struct.pack("<" + "h" * len(samples), *samples)
        return pygame.mixer.Sound(buffer=buf)
    except Exception:
        return None


class SoundManager:
    def __init__(self) -> None:
        self.win_sound: pygame.mixer.Sound | None = None
        self.lose_sound: pygame.mixer.Sound | None = None
        self._init_mixer()

    def _init_mixer(self) -> None:
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
            self.win_sound = generate_fanfare_sound()
            self.lose_sound = generate_womp_womp_sound()
        except Exception:
            pass

    def play_win(self) -> None:
        if self.win_sound:
            try:
                self.win_sound.play()
            except Exception:
                pass

    def play_lose(self) -> None:
        if self.lose_sound:
            try:
                self.lose_sound.play()
            except Exception:
                pass
