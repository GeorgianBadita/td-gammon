from __future__ import annotations
import copy
import random
import backgammon.agent.agent as agent
from collections import namedtuple
from enum import Enum
from typing import List, Optional, Tuple


class MoveType(Enum):
    NORMAL = 0
    BAR_ENTRY = 1
    BEAR_OFF = 2


Move = namedtuple("Move", "from_point to_point move_type")
BarredPieces = namedtuple("Barred", "white black")
OffedPieces = namedtuple("Offed", "white black")


class MoveRoll:
    def __init__(self, moves: List[Move]) -> "MoveRoll":
        self.__moves = moves

    @property
    def moves(self) -> List[Move]:
        return self.__moves


class BoardState(Enum):
    NORMAL = 0
    BARRED_PIECES = 1
    BEAR_OFF = 2
    OVER = 3


class Player(Enum):
    WHITE = 0
    BLACK = 1

    @classmethod
    def get_str_repr(_, pl: "Player") -> str:
        return "w" if pl == Player.WHITE else "b"

    @classmethod
    def get_player_from_str_repr(_, str_repr: str) -> "Player":
        if str_repr not in ["b", "w"]:
            raise ValueError(
                f"{str_repr} is not a valid string representation for Player"
            )

        return Player.WHITE if str_repr == "w" else Player.BLACK

    @classmethod
    def get_home_board_range(_, pl: "Player") -> List[int]:
        if pl == Player.WHITE:
            return list(range(6))
        else:
            return list(range(23, 17, -1))


class Board:
    """
    Class for representing a backgammon board
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
    ) -> "Board":
        # points[idx] = {-n, if there are n black checkers at idxth point,
        # n if there are n white checkers at idxth point. 0 <= idx < 24
        self.__points = points
        self.__turn = turn
        self.__barred_white = barred_white
        self.__barred_black = barred_black
        self.__offed_white = offed_white
        self.__offed_black = offed_black

    @property
    def points(self) -> List[int]:
        return self.__points

    @property
    def turn(self) -> Player:
        return self.__turn

    @turn.setter
    def turn(self, new_turn: Player):
        self.__turn = new_turn

    @property
    def barred(self) -> BarredPieces:
        return BarredPieces(self.__barred_white, self.__barred_black)

    @property
    def offed(self) -> OffedPieces:
        return OffedPieces(self.__offed_white, self.__offed_black)

    @property
    def is_game_over(self) -> bool:
        return (
            self.__offed_black == Board.INIT_CHECKER_COUNT
            or self.__offed_white == Board.INIT_CHECKER_COUNT
        )

    @property
    def game_state_for_current_turn(self) -> BoardState:
        if self.is_game_over:
            return BoardState.OVER
        if (self.__turn == Player.WHITE and self.__barred_white > 0) or (
            self.__turn == Player.BLACK and self.__barred_black > 0
        ):
            return BoardState.BARRED_PIECES
        if self.__all_pieces_in_house_for_turn():
            return BoardState.BEAR_OFF
        return BoardState.NORMAL

    @property
    def winner(self) -> Optional[Player]:
        if self.__offed_black == Board.INIT_CHECKER_COUNT:
            return Player.BLACK
        elif self.__offed_white == Board.INIT_CHECKER_COUNT:
            return Player.WHITE
        return None

    def roll_dice(self) -> Tuple[int, int]:
        """
        Function that rolls a dice
        @return tuple of (int, int), with each int <= 6
        """
        return (random.randint(1, 6), random.randint(1, 6))

    def clone(self) -> "Board":
        point_copy = copy.deepcopy(self.__points)
        return Board(
            point_copy,
            self.__turn,
            self.__barred_white,
            self.__barred_black,
            self.__offed_white,
            self.__offed_black,
        )

    def serialize_board(self) -> str:
        """
        Function for serializing a backgammon board position
        The board is encoded similarly to chess FEN notation
        e.g. 1-2-b/6-5-w/8-3-w/12-5-b/13-5-w/17-3-b/19-5-b/24-2-w w 0 0 0 0
        represents the satart position for backgammon game
        groups a-b-c mean: there are b checkers of c color on point a
        after all the a-b-c groups, there is a letter representing the current player
        turn, w for WHITE, b for BLACK. After the turn encoding, there are 2 groups of 2 numbers,
        first two numbers represent the number of barred pieces, first for white, then for black.
        Finnally the last 2 numbers represent the number of offloaded pieces for each player,
        first for white then for black.
        @return: returns the serialized board to string
        """

        checkers = []
        for idx in range(Board.NUM_PLAYABLE_POINTS):
            if not self.__is_empty_point(idx):
                point, count, side = (
                    idx,
                    self.__points[idx],
                    Player.get_str_repr(Player.WHITE),
                )
                if self.__is_point_of_color(idx, Player.BLACK):
                    count, side = -self.__points[idx], Player.get_str_repr(Player.BLACK)
                checkers.append(f"{point+1}-{count}-{side}")
        checkers_str = "/".join(checkers)
        return " ".join(
            [
                checkers_str,
                Player.get_str_repr(self.__turn),
                f"{self.__barred_white} {self.__barred_black}",
                f"{self.__offed_white} {self.__offed_black}",
            ]
        )

    @classmethod
    def from_string(_: "Board", serialized_board: str) -> "Board":
        """
        Function for deserializing a string board position into a backgammon
        board object.
        The board is encoded similarly to chess FEN notation
        e.g. 1-2-b/6-5-w/8-3-w/12-5-b/13-5-w/17-3-b/19-5-b/25-2-w w 0 0 0 0
        represents the satart position for backgammon game
        groups a-b-c mean: there are b checkers of c color on point a
        after all the a-b-c groups, there is a letter representing the current player
        turn, w for WHITE, b for BLACK. After the turn encoding, there are 2 groups of 2 numbers,
        first two numbers represent the number of barred pieces, first for white, then for black.
        Finnally the last 2 numbers represent the number of offloaded pieces for each player,
        first for white then for black.
        @return: return the deserialized backgammon game
        """

        (
            checkers_str,
            turn,
            barred_white,
            barred_black,
            offed_white,
            offed_black,
        ) = serialized_board.split(" ")
        points = [0] * Board.NUM_PLAYABLE_POINTS
        for part in checkers_str.split("/"):
            point, checker_count, side = part.split("-")
            if side == "w":
                points[int(point) - 1] = int(checker_count)
            else:
                points[int(point) - 1] = -int(checker_count)

        return Board(
            points,
            Player.get_player_from_str_repr(turn),
            int(barred_white),
            int(barred_black),
            int(offed_white),
            int(offed_black),
        )

    @classmethod
    def new_board(
        cls: "Board",
        starting_player=Player.WHITE,
    ) -> "Board":
        """
        Function for starting a new fresh backgammon board
        given the starting agent
        """
        if starting_player.player == Player.WHITE:
            return cls.from_string(cls.STARTING_BOARD_SERIALIZED_STARTING_WHITE)
        return cls.from_string(cls.STARTING_BOARD_SERIALIZED_STARTING_BLACK)

    def __is_empty_point(self, idx: int) -> bool:
        return self.__points[idx] == 0

    def __is_point_of_color(self, idx: int, color: Player) -> bool:
        return (color == Player.WHITE and self.__points[idx] > 0) or (
            color == Player.BLACK and self.__points[idx] < 0
        )

    def __all_pieces_in_house_for_turn(self) -> bool:
        """
        Checks if current player can bear off pieces (essentially if all of their home pieces
            + all of their already bord off pieces add up to 15
        )
        """
        cnt = 0
        for idx in Player.get_home_board_range(self.__turn):
            cnt += (
                self.__points[idx]
                if self.__turn == Player.WHITE
                else -self.__points[idx]
            )

        offed_pieces = (
            self.__offed_white if self.__turn == Player.WHITE else self.__offed_black
        )
        return cnt + offed_pieces == Board.INIT_CHECKER_COUNT

    def __eq__(self: "Board", ot: "Board") -> bool:
        return (
            self.points == ot.points
            and self.__turn == ot.turn
            and self.__barred_black == ot.__barred_black
            and self.__barred_white == ot.__barred_white
            and self.__offed_black == ot.__offed_black
            and self.__offed_white == ot.__offed_white
        )
