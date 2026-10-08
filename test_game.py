from __future__ import annotations

import random

import pygame

from ai import choose_column, choose_column_kids
from audio import SoundManager
from game import Board, Player, ScoreTracker
from main import key_to_column


def test_horizontal_win() -> None:
    board = Board()
    for col in range(3):
        board.drop(col, Player.RED)
        board.drop(col, Player.YELLOW)
    result = board.drop(3, Player.RED)
    assert result is not None and result.is_win
    assert (5, 0) in result.winning_cells


def test_vertical_win() -> None:
    board = Board()
    for _ in range(3):
        board.drop(0, Player.RED)
        board.drop(1, Player.YELLOW)
    result = board.drop(0, Player.RED)
    assert result is not None and result.is_win


def test_diagonal_win() -> None:
    board = Board()
    # Build a rising diagonal for Red: (5,0), (4,1), (3,2), (2,3)
    board.drop(0, Player.RED)
    board.drop(1, Player.YELLOW)
    board.drop(1, Player.RED)
    board.drop(2, Player.YELLOW)
    board.drop(2, Player.YELLOW)
    board.drop(3, Player.RED)
    board.drop(2, Player.RED)
    board.drop(3, Player.YELLOW)
    board.drop(3, Player.YELLOW)
    result = board.drop(3, Player.RED)
    assert result is not None and result.is_win


def test_full_column_rejected() -> None:
    board = Board()
    for i in range(6):
        player = Player.RED if i % 2 == 0 else Player.YELLOW
        assert board.drop(0, player) is not None
    assert board.drop(0, Player.RED) is None


def test_ai_takes_immediate_win() -> None:
    board = Board()
    # Yellow threatens (5,0)-(5,2); Red occupies elsewhere.
    board.drop(0, Player.YELLOW)
    board.drop(6, Player.RED)
    board.drop(1, Player.YELLOW)
    board.drop(6, Player.RED)
    board.drop(2, Player.YELLOW)
    board.drop(5, Player.RED)
    assert choose_column(board, Player.YELLOW, depth=4) == 3


def test_ai_blocks_immediate_loss() -> None:
    board = Board()
    board.drop(0, Player.RED)
    board.drop(6, Player.YELLOW)
    board.drop(1, Player.RED)
    board.drop(6, Player.YELLOW)
    board.drop(2, Player.RED)
    assert choose_column(board, Player.YELLOW, depth=4) == 3


class _AlwaysNotice:
    def random(self) -> float:
        return 0.0

    def choice(self, seq: list[int]) -> int:
        return seq[0]


def _horizontal_yellow_win_board() -> Board:
    board = Board()
    board.drop(0, Player.YELLOW)
    board.drop(6, Player.RED)
    board.drop(1, Player.YELLOW)
    board.drop(6, Player.RED)
    board.drop(2, Player.YELLOW)
    board.drop(5, Player.RED)
    return board


def _horizontal_red_threat_board() -> Board:
    board = Board()
    board.drop(0, Player.RED)
    board.drop(6, Player.YELLOW)
    board.drop(1, Player.RED)
    board.drop(6, Player.YELLOW)
    board.drop(2, Player.RED)
    return board


def test_kids_always_legal() -> None:
    board = Board()
    board.drop(3, Player.RED)
    for seed in range(40):
        col = choose_column_kids(board, Player.YELLOW, rng=random.Random(seed))
        assert col in board.valid_columns()


def test_kids_notices_immediate_win() -> None:
    board = _horizontal_yellow_win_board()
    assert choose_column_kids(board, Player.YELLOW, rng=_AlwaysNotice()) == 3


def test_kids_notices_horizontal_block() -> None:
    board = _horizontal_red_threat_board()
    assert choose_column_kids(board, Player.YELLOW, rng=_AlwaysNotice()) == 3


def test_ai_plays_as_red_takes_win() -> None:
    board = Board()
    board.drop(0, Player.RED)
    board.drop(6, Player.YELLOW)
    board.drop(1, Player.RED)
    board.drop(6, Player.YELLOW)
    board.drop(2, Player.RED)
    board.drop(5, Player.YELLOW)
    assert choose_column(board, Player.RED, depth=4) == 3


def test_kids_plays_as_red_takes_win() -> None:
    board = Board()
    board.drop(0, Player.RED)
    board.drop(6, Player.YELLOW)
    board.drop(1, Player.RED)
    board.drop(6, Player.YELLOW)
    board.drop(2, Player.RED)
    board.drop(5, Player.YELLOW)
    assert choose_column_kids(board, Player.RED, rng=_AlwaysNotice()) == 3


def test_sound_manager() -> None:
    sm = SoundManager()
    # Should not raise any exceptions even if audio driver is present or dummy
    sm.play_win()
    sm.play_lose()


def test_score_tracker() -> None:
    tracker = ScoreTracker()
    assert tracker.red_wins == 0
    assert tracker.yellow_wins == 0

    tracker.record_win(Player.RED)
    assert tracker.red_wins == 1
    assert tracker.yellow_wins == 0

    tracker.record_win(Player.YELLOW)
    tracker.record_win(Player.YELLOW)
    assert tracker.red_wins == 1
    assert tracker.yellow_wins == 2

    # Recording win for EMPTY should not increment either score
    tracker.record_win(Player.EMPTY)
    assert tracker.red_wins == 1
    assert tracker.yellow_wins == 2

    tracker.reset()
    assert tracker.red_wins == 0
    assert tracker.yellow_wins == 0


def test_key_to_column_mapping() -> None:
    # Standard top row numbers 1..7 -> cols 0..6
    for i in range(1, 8):
        key = getattr(pygame, f"K_{i}")
        assert key_to_column(key) == i - 1

    # Keypad numbers 1..7 -> cols 0..6
    for i in range(1, 8):
        key = getattr(pygame, f"K_KP{i}")
        assert key_to_column(key) == i - 1

    # Unmapped keys (0, 8, letters, etc.)
    assert key_to_column(pygame.K_0) is None
    assert key_to_column(pygame.K_8) is None
    assert key_to_column(pygame.K_a) is None


if __name__ == "__main__":
    test_horizontal_win()
    test_vertical_win()
    test_diagonal_win()
    test_full_column_rejected()
    test_ai_takes_immediate_win()
    test_ai_blocks_immediate_loss()
    test_kids_always_legal()
    test_kids_notices_immediate_win()
    test_kids_notices_horizontal_block()
    test_ai_plays_as_red_takes_win()
    test_kids_plays_as_red_takes_win()
    test_key_to_column_mapping()
    test_score_tracker()
    test_sound_manager()
    print("logic tests passed")
