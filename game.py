"""Pure Connect 4 rules: board state, moves, and win detection."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Iterable

from constants import COLS, ROWS


class GameMode(IntEnum):
    KIDS = 1
    CLASSIC = 2
    TWO_PLAYER = 3

    @property
    def vs_ai(self) -> bool:
        return self is not GameMode.TWO_PLAYER

    @property
    def ai_label(self) -> str | None:
        if self is GameMode.KIDS:
            return "Kids AI"
        if self is GameMode.CLASSIC:
            return "AI"
        return None


class Player(IntEnum):
    EMPTY = 0
    RED = 1
    YELLOW = 2

    @property
    def opponent(self) -> Player:
        if self is Player.RED:
            return Player.YELLOW
        if self is Player.YELLOW:
            return Player.RED
        return Player.EMPTY

    @property
    def label(self) -> str:
        return {Player.RED: "Red", Player.YELLOW: "Yellow", Player.EMPTY: "None"}[self]


@dataclass(frozen=True)
class MoveResult:
    row: int
    col: int
    player: Player
    winning_cells: tuple[tuple[int, int], ...] = ()
    is_draw: bool = False

    @property
    def is_win(self) -> bool:
        return bool(self.winning_cells)


@dataclass
class Board:
    rows: int = ROWS
    cols: int = COLS
    grid: list[list[Player]] = field(init=False)

    def __post_init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.grid = [[Player.EMPTY for _ in range(self.cols)] for _ in range(self.rows)]

    def clone(self) -> Board:
        copy = Board(self.rows, self.cols)
        copy.grid = [row[:] for row in self.grid]
        return copy

    def valid_columns(self) -> list[int]:
        return [col for col in range(self.cols) if self.is_column_open(col)]

    def is_column_open(self, col: int) -> bool:
        return 0 <= col < self.cols and self.grid[0][col] is Player.EMPTY

    def undo(self, row: int, col: int) -> None:
        self.grid[row][col] = Player.EMPTY

    def next_open_row(self, col: int) -> int | None:
        if not (0 <= col < self.cols):
            return None
        for row in range(self.rows - 1, -1, -1):
            if self.grid[row][col] is Player.EMPTY:
                return row
        return None

    def drop(self, col: int, player: Player) -> MoveResult | None:
        row = self.next_open_row(col)
        if row is None:
            return None
        self.grid[row][col] = player
        winning = self.winning_line(row, col, player)
        is_draw = not winning and self.is_full()
        return MoveResult(row=row, col=col, player=player, winning_cells=winning, is_draw=is_draw)

    def is_full(self) -> bool:
        return all(cell is not Player.EMPTY for cell in self.grid[0])

    def winning_line(self, row: int, col: int, player: Player) -> tuple[tuple[int, int], ...]:
        for direction in ((0, 1), (1, 0), (1, 1), (1, -1)):
            line = self._line_from(row, col, player, direction)
            if len(line) >= 4:
                return tuple(line)
        return ()

    def _line_from(
        self,
        row: int,
        col: int,
        player: Player,
        direction: tuple[int, int],
    ) -> list[tuple[int, int]]:
        dr, dc = direction
        cells = [(row, col)]
        cells.extend(self._ray(row, col, player, dr, dc))
        cells.extend(self._ray(row, col, player, -dr, -dc))
        cells.sort()
        return cells

    def _ray(
        self,
        row: int,
        col: int,
        player: Player,
        dr: int,
        dc: int,
    ) -> Iterable[tuple[int, int]]:
        r, c = row + dr, col + dc
        while 0 <= r < self.rows and 0 <= c < self.cols and self.grid[r][c] is player:
            yield (r, c)
            r += dr
            c += dc
