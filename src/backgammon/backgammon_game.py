from __future__ import annotations
import copy
import random
import backgammon.agent.agent as agent
from collections import namedtuple
from enum import Enum
from typing import List

from backgammon.board import Board, Player


class MoveType(Enum):
    NORMAL = 0
    BAR_ENTRY = 1
    BEAR_OFF = 2


Move = namedtuple("Move", "from_point to_point move_type")


class MoveRoll:
    def __init__(self, moves: List[Move]) -> "MoveRoll":
        self.__moves = moves

    @property
    def moves(self) -> List[Move]:
        return self.__moves


class BackgammonGame:
    """
    Class for representing a backgammon game
    """

    TOKENS: List[str] = ["o", "x"]
    STARTING_BOARD_SERIALIZED_STARTING_WHITE = (
        f"1-2-b/6-5-w/8-3-w/12-5-b/13-5-w/17-3-b/19-5-b/24-2-w w 0 0 0 0"
    )
    STARTING_BOARD_SERIALIZED_STARTING_BLACK = (
        f"1-2-b/6-5-w/8-3-w/12-5-b/13-5-w/17-3-b/19-5-b/24-2-w b 0 0 0 0"
    )
    NUM_PLAYABLE_POINTS: int = 24
    INIT_CHECKER_COUNT: int = 15

    def __init__(
        self,
        points: List[int],
        turn: Player,
        barred_white: int,
        barred_black: int,
        offed_white: int,
        offed_black: int,
        white_player_agent: agent.Agent,
        black_player_agent: agent.Agent,
    ) -> "BackgammonGame":
        # points[idx] = {-n, if there are n black checkers at idxth point,
        # n if there are n white checkers at idxth point. 0 <= idx < 24
        self.__board = Board(
            points, turn, barred_white, barred_black, offed_white, offed_black
        )
        self.__white_player_agent = white_player_agent
        self.__black_player_agent = black_player_agent

    @property
    def board(self) -> Board:
        return self.__board

    @property
    def white_player_agent(self) -> agent.Agent:
        return self.__white_player_agent

    @property
    def black_player_agent(self) -> agent.Agent:
        return self.__black_player_agent

    def play(self) -> Player:
        """
        Function that plays a game until it finishes
        """
        while not self.is_game_over:
            self.play_turn()
            self.board.turn = (
                Player.WHITE if self.__turn == Player.BLACK else Player.BLACK
            )

        winner = self.winner
        if winner is None:
            raise ValueError(
                "Something is wrong, game neded without a winner, winner is None"
            )
        return winner

    def play_turn(self):
        die_roll = self.roll_dice()
        move_rolls = self.get_possible_move_rolls()

        if self.board.turn == Player.WHITE:
            selected_move = self.__white_player_agent.get_move(move_rolls)
        else:
            selected_move = self.__black_player_agent.get_move(move_rolls)
        
        self.apply_move_roll(selected_move)

    def get_possible_move_rolls(self) -> List[MoveRoll]:
        pass

    def apply_move_roll(self, mv: MoveRoll):
        pass

    def undo_move_roll(self, mv: MoveRoll):
        pass

    def clone(self) -> "BackgammonGame":
        point_copy = copy.deepcopy(self.__points)
        return BackgammonGame(
            point_copy,
            self.__turn,
            self.__barred_white,
            self.__barred_black,
            self.__offed_white,
            self.__offed_black,
        )

    @classmethod
    def new_game(
        cls: "BackgammonGame",
        white_agent: agent.Agent,
        black_agent: agent.Agent,
        starting_player=Player.WHITE,
    ) -> "BackgammonGame":
        """
        Function for starting a new fresh backgammon game
        given the starting agents
        """
        if starting_player == Player.WHITE:
            board = Board.from_string(Board.STARTING_BOARD_SERIALIZED_STARTING_WHITE)
        else:
            board = Board.from_string(Board.STARTING_BOARD_SERIALIZED_STARTING_BLACK)

        return BackgammonGame(
            board.points,
            board.turn,
            *board.barred,
            *board.offed,
            white_agent,
            black_agent,
        )

    def __is_empty_point(self, idx: int) -> bool:
        return self.__points[idx] == 0

    def __is_point_of_color(self, idx: int, color: Player) -> bool:
        return (color == Player.WHITE and self.__points[idx] > 0) or (
            color == Player.BLACK and self.__points[idx] < 0
        )

    def __eq__(self: "BackgammonGame", ot: "BackgammonGame") -> bool:
        return (
            self.__board == ot.board
            and self.__white_player_agent == ot.white_player_agent
            and self.__black_player_agent == ot.black_player_agent
        )
