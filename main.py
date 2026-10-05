"""Connect 4 game loop: menu, input, drop animation, hover preview, and AI."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

import pygame

from ai import choose_column, choose_column_kids
from constants import (
    AI_THINK_DELAY_MS,
    DROP_DURATION_MS,
    FPS,
    HEADER_HEIGHT,
    WIN_PULSE_MS,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from game import Board, GameMode, MoveResult, Player
from renderer import Renderer, cell_center, column_from_x


class Screen(Enum):
    MENU = auto()
    ORDER_SELECT = auto()
    PLAY = auto()


MENU_KEYS = {
    pygame.K_1: GameMode.KIDS,
    pygame.K_2: GameMode.CLASSIC,
    pygame.K_3: GameMode.TWO_PLAYER,
}

MENU_BUTTON_MODES = {
    "kids": GameMode.KIDS,
    "classic": GameMode.CLASSIC,
    "multi": GameMode.TWO_PLAYER,
}

KEY_TO_COL = {
    pygame.K_1: 0,
    pygame.K_2: 1,
    pygame.K_3: 2,
    pygame.K_4: 3,
    pygame.K_5: 4,
    pygame.K_6: 5,
    pygame.K_7: 6,
    pygame.K_KP1: 0,
    pygame.K_KP2: 1,
    pygame.K_KP3: 2,
    pygame.K_KP4: 3,
    pygame.K_KP5: 4,
    pygame.K_KP6: 5,
    pygame.K_KP7: 6,
}


def key_to_column(key: int) -> int | None:
    return KEY_TO_COL.get(key)


def ease_out_cubic(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1.0 - (1.0 - t) ** 3


@dataclass
class DropAnimation:
    col: int
    target_row: int
    player: Player
    start_y: float
    end_y: float
    elapsed_ms: float = 0.0

    def advance(self, dt_ms: float) -> float:
        self.elapsed_ms += dt_ms
        t = ease_out_cubic(self.elapsed_ms / DROP_DURATION_MS)
        return self.start_y + (self.end_y - self.start_y) * t

    def done(self) -> bool:
        return self.elapsed_ms >= DROP_DURATION_MS


def start_drop(board: Board, col: int, player: Player) -> DropAnimation | None:
    row = board.next_open_row(col)
    if row is None:
        return None
    return DropAnimation(
        col=col,
        target_row=row,
        player=player,
        start_y=HEADER_HEIGHT - 36,
        end_y=float(cell_center(row, col)[1]),
    )


def run() -> None:
    pygame.init()
    pygame.display.set_caption("Connect 4")
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()
    renderer = Renderer(screen)

    view = Screen.MENU
    mode = GameMode.TWO_PLAYER
    pending_mode: GameMode | None = None
    human_player = Player.RED
    ai_player = Player.YELLOW
    board = Board()
    current = Player.RED
    hover_col: int | None = None
    menu_hover: str | None = None
    order_hover: str | None = None
    animation: DropAnimation | None = None
    last_result: MoveResult | None = None
    game_over = False
    ai_delay_ms = 0.0
    pulse_ms = 0.0
    running = True
    menu_buttons: dict[str, pygame.Rect] = {}
    order_buttons: dict[str, pygame.Rect] = {}

    def reset_match() -> None:
        nonlocal board, current, animation, last_result, game_over, ai_delay_ms
        board.reset()
        current = Player.RED
        animation = None
        last_result = None
        game_over = False
        ai_delay_ms = 0.0

    def select_mode(selected: GameMode) -> None:
        nonlocal mode, pending_mode, view
        if selected.vs_ai:
            pending_mode = selected
            view = Screen.ORDER_SELECT
        else:
            mode = selected
            view = Screen.PLAY
            reset_match()

    def start_vs_ai(go_first: bool) -> None:
        nonlocal mode, human_player, ai_player, view
        assert pending_mode is not None
        mode = pending_mode
        if go_first:
            human_player = Player.RED
            ai_player = Player.YELLOW
        else:
            human_player = Player.YELLOW
            ai_player = Player.RED
        view = Screen.PLAY
        reset_match()

    while running:
        dt_ms = float(clock.tick(FPS))
        pulse_ms = (pulse_ms + dt_ms) % WIN_PULSE_MS
        pulse = pulse_ms / WIN_PULSE_MS
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if view is Screen.ORDER_SELECT:
                        view = Screen.MENU
                    else:
                        running = False
                elif view is Screen.MENU and event.key in MENU_KEYS:
                    select_mode(MENU_KEYS[event.key])
                elif view is Screen.ORDER_SELECT:
                    if event.key == pygame.K_1:
                        start_vs_ai(go_first=True)
                    elif event.key == pygame.K_2:
                        start_vs_ai(go_first=False)
                    elif event.key in (pygame.K_m, pygame.K_BACKSPACE):
                        view = Screen.MENU
                elif view is Screen.PLAY:
                    col = key_to_column(event.key)
                    if col is not None:
                        if (
                            animation is None
                            and not game_over
                            and not (mode.vs_ai and current is ai_player)
                        ):
                            animation = start_drop(board, col, current)
                    elif event.key == pygame.K_r:
                        reset_match()
                    elif event.key == pygame.K_m:
                        view = Screen.MENU
                        reset_match()
            elif event.type == pygame.MOUSEMOTION:
                hover_col = column_from_x(event.pos[0])
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if view is Screen.MENU:
                    for key, rect in menu_buttons.items():
                        if rect.collidepoint(event.pos):
                            selected = MENU_BUTTON_MODES.get(key)
                            if selected is not None:
                                select_mode(selected)
                            break
                elif view is Screen.ORDER_SELECT:
                    for key, rect in order_buttons.items():
                        if rect.collidepoint(event.pos):
                            if key == "first":
                                start_vs_ai(go_first=True)
                            elif key == "second":
                                start_vs_ai(go_first=False)
                            break
                elif (
                    animation is None
                    and not game_over
                    and not (mode.vs_ai and current is ai_player)
                ):
                    col = column_from_x(event.pos[0])
                    if col is not None:
                        animation = start_drop(board, col, current)

        if view is Screen.MENU:
            menu_hover = None
            for key, rect in menu_buttons.items():
                if rect.collidepoint(mouse_pos):
                    menu_hover = key
                    break
            renderer.draw_background()
            menu_buttons = renderer.draw_menu(menu_hover)
            pygame.display.flip()
            continue

        if view is Screen.ORDER_SELECT:
            order_hover = None
            for key, rect in order_buttons.items():
                if rect.collidepoint(mouse_pos):
                    order_hover = key
                    break
            renderer.draw_background()
            order_buttons = renderer.draw_order_menu(pending_mode, order_hover)
            pygame.display.flip()
            continue

        thinking = mode.vs_ai and current is ai_player and animation is None and not game_over
        if thinking:
            ai_delay_ms += dt_ms
            if ai_delay_ms >= AI_THINK_DELAY_MS:
                if mode is GameMode.KIDS:
                    ai_col = choose_column_kids(board, ai_player)
                else:
                    ai_col = choose_column(board, ai_player)
                animation = start_drop(board, ai_col, ai_player)
                ai_delay_ms = 0.0

        drop_y: float | None = None
        if animation is not None:
            drop_y = animation.advance(dt_ms)
            if animation.done():
                last_result = board.drop(animation.col, animation.player)
                if last_result is not None:
                    if last_result.is_win or last_result.is_draw:
                        game_over = True
                    else:
                        current = current.opponent
                        ai_delay_ms = 0.0
                animation = None
                drop_y = None

        human_turn = not (mode.vs_ai and current is ai_player)
        renderer.draw_background()
        renderer.draw_header(
            current=current if not (last_result and last_result.is_win) else last_result.player,
            game_over=game_over,
            winner=last_result.player if last_result and last_result.is_win else None,
            ai_label=mode.ai_label,
            thinking=thinking and animation is None,
            human_player=human_player,
        )
        renderer.draw_board(
            board=board,
            hover_col=None if animation or game_over or not human_turn else hover_col,
            current=current,
            animating=animation is not None,
            skip_cell=None,
            winning_cells=last_result.winning_cells if last_result else (),
            pulse=pulse,
        )
        if animation is not None and drop_y is not None:
            renderer.draw_dropping_disc(animation.col, drop_y, animation.player)
        if game_over and animation is None:
            renderer.draw_overlay(last_result.player if last_result and last_result.is_win else None)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    run()
