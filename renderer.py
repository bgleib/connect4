"""Pygame rendering for the board, discs, hover preview, and overlays."""

from __future__ import annotations

import math
from typing import Sequence

import pygame

from constants import (
    BG_BOTTOM,
    BG_TOP,
    BOARD_BLUE,
    BOARD_BLUE_DARK,
    BOARD_PADDING,
    CELL_SIZE,
    COLS,
    DISC_RADIUS,
    GOLD,
    HEADER_HEIGHT,
    HOLE_COLOR,
    HOLE_RADIUS,
    MUTED,
    OVERLAY,
    RED,
    RED_DARK,
    ROWS,
    WHITE,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
    YELLOW,
    YELLOW_DARK,
)
from game import Board, Player


def cell_center(row: int, col: int) -> tuple[int, int]:
    x = BOARD_PADDING + col * CELL_SIZE + CELL_SIZE // 2
    y = HEADER_HEIGHT + row * CELL_SIZE + CELL_SIZE // 2
    return x, y


def column_from_x(x: int) -> int | None:
    local = x - BOARD_PADDING
    if local < 0 or local >= COLS * CELL_SIZE:
        return None
    return local // CELL_SIZE


def lerp_color(
    start: tuple[int, int, int],
    end: tuple[int, int, int],
    t: float,
) -> tuple[int, int, int]:
    t = max(0.0, min(1.0, t))
    return (
        int(start[0] + (end[0] - start[0]) * t),
        int(start[1] + (end[1] - start[1]) * t),
        int(start[2] + (end[2] - start[2]) * t),
    )


class Renderer:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.title_font = pygame.font.SysFont("segoeui", 36, bold=True)
        self.body_font = pygame.font.SysFont("segoeui", 22)
        self.small_font = pygame.font.SysFont("segoeui", 16)

    def draw_background(self) -> None:
        for y in range(WINDOW_HEIGHT):
            t = y / max(WINDOW_HEIGHT - 1, 1)
            pygame.draw.line(self.screen, lerp_color(BG_TOP, BG_BOTTOM, t), (0, y), (WINDOW_WIDTH, y))

    def draw_header(
        self,
        current: Player,
        game_over: bool,
        winner: Player | None,
        ai_label: str | None,
        thinking: bool,
    ) -> None:
        title = self.title_font.render("Connect 4", True, WHITE)
        self.screen.blit(title, title.get_rect(midtop=(WINDOW_WIDTH // 2, 18)))

        if thinking:
            status = "Yellow is thinking..."
            color = YELLOW
        elif game_over and winner is not None:
            status = f"{winner.label} wins"
            color = RED if winner is Player.RED else YELLOW
        elif game_over:
            status = "Draw game"
            color = MUTED
        else:
            if ai_label and current is Player.YELLOW:
                status = f"Yellow ({ai_label})'s turn"
            elif ai_label:
                status = "Your turn (Red)"
            else:
                status = f"{current.label}'s turn"
            color = RED if current is Player.RED else YELLOW

        label = self.body_font.render(status, True, color)
        self.screen.blit(label, label.get_rect(center=(WINDOW_WIDTH // 2, 78)))

        hint_text = "Click a column  ·  R replay  ·  M menu  ·  Esc quit"
        hint = self.small_font.render(hint_text, True, MUTED)
        self.screen.blit(hint, hint.get_rect(center=(WINDOW_WIDTH // 2, 112)))

        if not game_over:
            pygame.draw.circle(self.screen, color, (WINDOW_WIDTH // 2 - 150, 78), 10)
            pygame.draw.circle(self.screen, color, (WINDOW_WIDTH // 2 + 150, 78), 10)

    def draw_menu(self, hover_key: str | None) -> dict[str, pygame.Rect]:
        title = self.title_font.render("Connect 4", True, WHITE)
        self.screen.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 86)))
        subtitle = self.body_font.render("Choose how you want to play", True, MUTED)
        self.screen.blit(subtitle, subtitle.get_rect(center=(WINDOW_WIDTH // 2, 132)))

        card_w, card_h, gap = 196, 180, 16
        total_w = 3 * card_w + 2 * gap
        start_x = (WINDOW_WIDTH - total_w) // 2
        buttons = {
            "kids": pygame.Rect(start_x, 240, card_w, card_h),
            "classic": pygame.Rect(start_x + card_w + gap, 240, card_w, card_h),
            "multi": pygame.Rect(start_x + 2 * (card_w + gap), 240, card_w, card_h),
        }
        copy = {
            "kids": ("Kids", "You are Red", "Gentle Yellow AI"),
            "classic": ("Classic", "You are Red", "Tactical Yellow AI"),
            "multi": ("Two Players", "Red vs Yellow", "Hot-seat on one PC"),
        }

        for key, rect in buttons.items():
            hovered = hover_key == key
            fill = BOARD_BLUE if hovered else BOARD_BLUE_DARK
            pygame.draw.rect(self.screen, fill, rect, border_radius=22)
            pygame.draw.rect(self.screen, GOLD if hovered else MUTED, rect, width=2, border_radius=22)
            heading, line1, line2 = copy[key]
            heading_surf = self.body_font.render(heading, True, WHITE)
            self.screen.blit(heading_surf, heading_surf.get_rect(center=(rect.centerx, rect.y + 48)))
            pygame.draw.circle(self.screen, RED, (rect.centerx - 16, rect.y + 92), 16)
            pygame.draw.circle(self.screen, YELLOW, (rect.centerx + 16, rect.y + 92), 16)
            detail1 = self.small_font.render(line1, True, MUTED)
            detail2 = self.small_font.render(line2, True, MUTED)
            self.screen.blit(detail1, detail1.get_rect(center=(rect.centerx, rect.y + 128)))
            self.screen.blit(detail2, detail2.get_rect(center=(rect.centerx, rect.y + 150)))

        footer = self.small_font.render("Click a mode or press 1 / 2 / 3", True, MUTED)
        self.screen.blit(footer, footer.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 48)))
        return buttons

    def draw_board(
        self,
        board: Board,
        hover_col: int | None,
        current: Player,
        animating: bool,
        skip_cell: tuple[int, int] | None,
        winning_cells: Sequence[tuple[int, int]],
        pulse: float,
    ) -> None:
        board_rect = pygame.Rect(
            BOARD_PADDING - 12,
            HEADER_HEIGHT - 12,
            COLS * CELL_SIZE + 24,
            ROWS * CELL_SIZE + 24,
        )
        pygame.draw.rect(self.screen, BOARD_BLUE_DARK, board_rect, border_radius=28)
        pygame.draw.rect(self.screen, BOARD_BLUE, board_rect.inflate(-10, -10), border_radius=22)

        landing_row = board.next_open_row(hover_col) if hover_col is not None and not animating else None
        if hover_col is not None and landing_row is not None:
            self._draw_disc(cell_center(landing_row, hover_col), current, alpha=70)

        win_set = set(winning_cells)
        for row in range(ROWS):
            for col in range(COLS):
                center = cell_center(row, col)
                pygame.draw.circle(self.screen, HOLE_COLOR, center, HOLE_RADIUS)
                if skip_cell == (row, col):
                    continue
                occupant = board.grid[row][col]
                if occupant is Player.EMPTY:
                    continue
                glow = 1.0
                if (row, col) in win_set:
                    glow = 0.55 + 0.45 * (0.5 + 0.5 * math.sin(pulse * math.tau))
                self._draw_disc(center, occupant, glow=glow)

    def draw_dropping_disc(self, col: int, y: float, player: Player) -> None:
        x = BOARD_PADDING + col * CELL_SIZE + CELL_SIZE // 2
        self._draw_disc((int(x), int(y)), player)

    def draw_overlay(self, winner: Player | None) -> None:
        banner_rect = pygame.Rect(36, WINDOW_HEIGHT - 64, WINDOW_WIDTH - 72, 48)
        veil = pygame.Surface(banner_rect.size, pygame.SRCALPHA)
        veil.fill(OVERLAY)
        self.screen.blit(veil, banner_rect.topleft)
        pygame.draw.rect(self.screen, GOLD, banner_rect, width=1, border_radius=12)

        message = "Draw — R replay  ·  M menu" if winner is None else f"{winner.label} connects 4!  R replay  ·  M menu"
        color = MUTED if winner is None else (RED if winner is Player.RED else YELLOW)
        prompt = self.body_font.render(message, True, color)
        self.screen.blit(prompt, prompt.get_rect(center=banner_rect.center))

    def _draw_disc(
        self,
        center: tuple[int, int],
        player: Player,
        *,
        alpha: int | None = None,
        glow: float = 1.0,
    ) -> None:
        fill, shade = (RED, RED_DARK) if player is Player.RED else (YELLOW, YELLOW_DARK)
        fill = lerp_color(shade, fill, glow)

        if alpha is not None:
            disc = pygame.Surface((DISC_RADIUS * 2 + 8, DISC_RADIUS * 2 + 8), pygame.SRCALPHA)
            local = (DISC_RADIUS + 4, DISC_RADIUS + 4)
            pygame.draw.circle(disc, (*shade, alpha), local, DISC_RADIUS)
            pygame.draw.circle(disc, (*fill, alpha), (local[0] - 3, local[1] - 3), DISC_RADIUS - 4)
            pygame.draw.circle(disc, (255, 255, 255, max(20, alpha // 4)), (local[0] - 12, local[1] - 14), 10)
            self.screen.blit(disc, disc.get_rect(center=center))
            return

        pygame.draw.circle(self.screen, shade, center, DISC_RADIUS)
        pygame.draw.circle(self.screen, fill, (center[0] - 3, center[1] - 3), DISC_RADIUS - 4)
        pygame.draw.circle(self.screen, (255, 255, 255), (center[0] - 12, center[1] - 14), 10)
        if glow > 1.0 or glow != 1.0:
            ring = GOLD if glow != 1.0 else fill
            pygame.draw.circle(self.screen, ring, center, DISC_RADIUS + 3, 3)
