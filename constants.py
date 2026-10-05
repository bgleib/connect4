"""Layout, colors, and animation constants for the Connect 4 UI."""

from __future__ import annotations

from typing import Final

ROWS: Final[int] = 6
COLS: Final[int] = 7

CELL_SIZE: Final[int] = 96
BOARD_PADDING: Final[int] = 24
HEADER_HEIGHT: Final[int] = 140
FOOTER_HEIGHT: Final[int] = 72

BOARD_WIDTH: Final[int] = COLS * CELL_SIZE
BOARD_HEIGHT: Final[int] = ROWS * CELL_SIZE
WINDOW_WIDTH: Final[int] = BOARD_WIDTH + BOARD_PADDING * 2
WINDOW_HEIGHT: Final[int] = HEADER_HEIGHT + BOARD_HEIGHT + FOOTER_HEIGHT + BOARD_PADDING

DISC_RADIUS: Final[int] = 38
HOLE_RADIUS: Final[int] = 42

FPS: Final[int] = 60
DROP_DURATION_MS: Final[int] = 420
WIN_PULSE_MS: Final[int] = 900
AI_DEPTH: Final[int] = 5
AI_THINK_DELAY_MS: Final[int] = 220
KIDS_TAKE_WIN: Final[float] = 0.80
KIDS_BLOCK_HORIZONTAL: Final[float] = 0.75
KIDS_BLOCK_VERTICAL: Final[float] = 0.75
KIDS_BLOCK_DIAGONAL: Final[float] = 0.60

# Palette
BG_TOP: Final[tuple[int, int, int]] = (12, 18, 38)
BG_BOTTOM: Final[tuple[int, int, int]] = (22, 32, 62)
BOARD_BLUE: Final[tuple[int, int, int]] = (28, 86, 196)
BOARD_BLUE_DARK: Final[tuple[int, int, int]] = (18, 58, 142)
HOLE_COLOR: Final[tuple[int, int, int]] = (10, 16, 34)
RED: Final[tuple[int, int, int]] = (230, 57, 70)
RED_DARK: Final[tuple[int, int, int]] = (168, 28, 42)
YELLOW: Final[tuple[int, int, int]] = (255, 209, 64)
YELLOW_DARK: Final[tuple[int, int, int]] = (201, 148, 18)
WHITE: Final[tuple[int, int, int]] = (244, 247, 255)
MUTED: Final[tuple[int, int, int]] = (168, 180, 214)
GOLD: Final[tuple[int, int, int]] = (255, 214, 102)
OVERLAY: Final[tuple[int, int, int, int]] = (8, 12, 28, 170)
