"""Minimax Connect 4 search plus a weaker Kids-mode policy."""

from __future__ import annotations

import random
from collections.abc import Sequence

from constants import (
    AI_DEPTH,
    COLS,
    KIDS_BLOCK_DIAGONAL,
    KIDS_BLOCK_HORIZONTAL,
    KIDS_BLOCK_VERTICAL,
    KIDS_TAKE_WIN,
    ROWS,
)
from game import Board, Player

CENTER_COLUMN = COLS // 2
COLUMN_ORDER = sorted(range(COLS), key=lambda col: abs(col - CENTER_COLUMN))

WIN_SCORE = 1_000_000


def choose_column(board: Board, player: Player = Player.YELLOW, depth: int = AI_DEPTH) -> int:
    """Return the tactically best open column for `player`."""
    valid = [col for col in COLUMN_ORDER if board.is_column_open(col)]
    if not valid:
        raise ValueError("No legal moves remain")

    best_col = valid[0]
    best_score = -WIN_SCORE * 10
    alpha = -WIN_SCORE * 10
    beta = WIN_SCORE * 10

    for col in valid:
        row = board.next_open_row(col)
        if row is None:
            continue
        result = board.drop(col, player)
        assert result is not None
        if result.is_win:
            score = WIN_SCORE
        elif result.is_draw:
            score = 0
        else:
            score = _minimax(board, depth - 1, alpha, beta, False, player)
        board.undo(result.row, result.col)
        if score > best_score:
            best_score = score
            best_col = col
        alpha = max(alpha, best_score)
    return best_col


def choose_column_kids(
    board: Board,
    player: Player = Player.YELLOW,
    rng: random.Random | None = None,
) -> int:
    """Pick a legal column with kid-like tactics: often take wins, sometimes block."""
    rng = rng or random.Random()
    valid = board.valid_columns()
    if not valid:
        raise ValueError("No legal moves remain")

    wins = _immediate_wins(board, player)
    if wins and rng.random() < KIDS_TAKE_WIN:
        return rng.choice(wins)

    threats = _immediate_threats(board, player.opponent)
    threats.sort(key=lambda item: _BLOCK_PRIORITY[item[1]])
    for col, kind in threats:
        if rng.random() < _BLOCK_CHANCE[kind]:
            return col

    return _weighted_play(board, player, valid, rng)


def _immediate_wins(board: Board, player: Player) -> list[int]:
    columns: list[int] = []
    for col in board.valid_columns():
        result = board.drop(col, player)
        if result is not None:
            if result.is_win:
                columns.append(col)
            board.undo(result.row, result.col)
    return columns


def _immediate_threats(board: Board, opponent: Player) -> list[tuple[int, str]]:
    threats: list[tuple[int, str]] = []
    for col in board.valid_columns():
        result = board.drop(col, opponent)
        if result is not None:
            if result.is_win:
                threats.append((col, _line_kind(result.winning_cells)))
            board.undo(result.row, result.col)
    return threats


def _line_kind(cells: Sequence[tuple[int, int]]) -> str:
    rows = {row for row, _col in cells}
    cols = {col for _row, col in cells}
    if len(rows) == 1:
        return "horizontal"
    if len(cols) == 1:
        return "vertical"
    return "diagonal"


_BLOCK_CHANCE = {
    "horizontal": KIDS_BLOCK_HORIZONTAL,
    "vertical": KIDS_BLOCK_VERTICAL,
    "diagonal": KIDS_BLOCK_DIAGONAL,
}
_BLOCK_PRIORITY = {"horizontal": 0, "vertical": 1, "diagonal": 2}


def _weighted_play(board: Board, player: Player, valid: list[int], rng: random.Random) -> int:
    weights = [_column_weight(board, player, col) for col in valid]
    total = sum(weights)
    pick = rng.random() * total
    acc = 0.0
    for col, weight in zip(valid, weights, strict=True):
        acc += weight
        if pick <= acc:
            return col
    return valid[-1]


def _column_weight(board: Board, player: Player, col: int) -> float:
    row = board.next_open_row(col)
    if row is None:
        return 0.01
    weight = 1.0 + 3.0 * (1.0 - abs(col - CENTER_COLUMN) / CENTER_COLUMN)
    if row < ROWS - 1:
        weight += 2.0
    result = board.drop(col, player)
    if result is not None:
        twos = 0
        for window in _windows(board):
            if window.count(player) == 2 and window.count(Player.EMPTY) == 2:
                twos += 1
        weight += twos * 0.35
        board.undo(result.row, result.col)
    return max(weight, 0.05)


def _minimax(
    board: Board,
    depth: int,
    alpha: int,
    beta: int,
    maximizing: bool,
    ai_player: Player,
) -> int:
    human = ai_player.opponent
    valid = [col for col in COLUMN_ORDER if board.is_column_open(col)]
    if not valid:
        return 0
    if depth == 0:
        return evaluate(board, ai_player)

    if maximizing:
        value = -WIN_SCORE * 10
        for col in valid:
            result = board.drop(col, ai_player)
            assert result is not None
            if result.is_win:
                score = WIN_SCORE + depth
            elif result.is_draw:
                score = 0
            else:
                score = _minimax(board, depth - 1, alpha, beta, False, ai_player)
            board.undo(result.row, result.col)
            value = max(value, score)
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value

    value = WIN_SCORE * 10
    for col in valid:
        result = board.drop(col, human)
        assert result is not None
        if result.is_win:
            score = -WIN_SCORE - depth
        elif result.is_draw:
            score = 0
        else:
            score = _minimax(board, depth - 1, alpha, beta, True, ai_player)
        board.undo(result.row, result.col)
        value = min(value, score)
        beta = min(beta, value)
        if alpha >= beta:
            break
    return value


def evaluate(board: Board, ai_player: Player) -> int:
    """Heuristic: center control plus 2-in-a-row / 3-in-a-row windows."""
    human = ai_player.opponent
    score = 0
    center_count = sum(1 for row in board.grid if row[CENTER_COLUMN] is ai_player)
    score += center_count * 6

    for window in _windows(board):
        score += _score_window(window, ai_player, human)
    return score


def _windows(board: Board) -> list[list[Player]]:
    windows: list[list[Player]] = []
    grid = board.grid

    for row in range(ROWS):
        for col in range(COLS - 3):
            windows.append(grid[row][col : col + 4])

    for col in range(COLS):
        for row in range(ROWS - 3):
            windows.append([grid[row + i][col] for i in range(4)])

    for row in range(ROWS - 3):
        for col in range(COLS - 3):
            windows.append([grid[row + i][col + i] for i in range(4)])
            windows.append([grid[row + 3 - i][col + i] for i in range(4)])
    return windows


def _score_window(window: list[Player], ai_player: Player, human: Player) -> int:
    ai_count = window.count(ai_player)
    human_count = window.count(human)
    empty = window.count(Player.EMPTY)

    if ai_count == 4:
        return 1000
    if human_count == 4:
        return -1000
    if ai_count == 3 and empty == 1:
        return 80
    if human_count == 3 and empty == 1:
        return -90
    if ai_count == 2 and empty == 2:
        return 12
    if human_count == 2 and empty == 2:
        return -10
    return 0
