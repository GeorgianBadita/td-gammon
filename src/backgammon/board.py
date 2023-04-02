from __future__ import annotations

from collections import namedtuple
from enum import Enum
from typing import List

from src.backgammon.agent import agent

BarredPieces = namedtuple("Barred", "white black")
OffedPieces = namedtuple("Offed", "white black")


class Player(Enum):
    WHITE = 0
    BLACK = 1

    @classmethod
    def get_str_repr(cls, pl: "Player") -> str:
        return "w" if pl == Player.WHITE else "b"

    @classmethod
    def get_player_from_str_repr(cls, str_repr: str) -> "Player":
        if str_repr not in ["b", "w"]:
            raise ValueError(
                f"{str_repr} is not a valid string representation for Player"
            )

        return Player.WHITE if str_repr == "w" else Player.BLACK

    @classmethod
    def get_home_board_range(cls, pl: "Player") -> List[int]:
        if pl == Player.WHITE:
            return list(range(6))
        else:
            return list(range(23, 17, -1))

    @classmethod
    def get_token(cls, pl: "Player") -> str:
        return "o" if pl == Player.WHITE else "x"


class Board:
    """
    Class for representing a backgammon board
    """

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
    ):
        # points[idx] = {-n, if there are n black checkers at idx-th point,
        # n if there are n white checkers at idx-th point. 0 <= idx < 24
        self.points = points
        self.__turn = turn
        self.__barred_white = barred_white
        self.__barred_black = barred_black
        self.__offed_white = offed_white
        self.__offed_black = offed_black

    @property
    def points(self) -> List[int]:
        return self.__points

    @points.setter
    def points(self, new_points: List[int]):
        self.__points = new_points

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

    def inc_offed(self, pl: Player):
        if pl == Player.WHITE:
            self.__offed_white += 1
        else:
            self.__offed_black += 1

    def dec_offed(self, pl: Player):
        if pl == Player.WHITE:
            self.__offed_white -= 1
        else:
            self.__offed_black -= 1

    def inc_barred(self, pl: Player):
        if pl == Player.WHITE:
            self.__barred_white += 1
        else:
            self.__barred_black += 1

    def dec_barred(self, pl: Player):
        if pl == Player.WHITE:
            self.__barred_white -= 1
        else:
            self.__barred_black -= 1

    def inc_point(self, idx: int):
        self.__points[idx] += 1

    def dec_point(self, idx: int):
        self.__points[idx] -= 1

    def num_checkers_at_index(self, idx: int) -> int:
        return abs(self.__points[idx])

    def index_in_home(self, idx: int, pl: Player) -> bool:
        match pl:
            case Player.WHITE:
                return 0 <= idx <= 5
            case Player.BLACK:
                return 18 <= idx <= 23

    def serialize_board(self) -> str:
        """
        Function for serializing a backgammon board position
        The board is encoded similarly to chess FEN notation
        e.g. 1-2-b/6-5-w/8-3-w/12-5-b/13-5-w/17-3-b/19-5-b/24-2-w w 0 0 0 0
        represents the starting position for backgammon game
        groups a-b-c mean: there are b checkers of c color on point an
        after all the a-b-c groups, there is a letter representing the current player
        turn, w for WHITE, b for BLACK. After the turn encoding, there are 2 groups of 2 numbers,
        first two numbers represent the number of barred pieces, first for white, then for black.
        Finally, the last 2 numbers represent the number of offloaded pieces for each player,
        first for white then for black.
        @return: returns the serialized board to string
        """

        checkers = []
        for idx in range(Board.NUM_PLAYABLE_POINTS):
            if not self.is_empty_point(idx):
                point, count, side = (
                    idx,
                    self.__points[idx],
                    Player.get_str_repr(Player.WHITE),
                )
                if self.is_point_of_color(idx, Player.BLACK):
                    count, side = - \
                        self.__points[idx], Player.get_str_repr(Player.BLACK)
                checkers.append(f"{point + 1}-{count}-{side}")
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
    def from_string(cls: "Board", serialized_board: str) -> "Board":
        """
        Function for deserializing a string board position into a backgammon
        board object.
        The board is encoded similarly to chess FEN notation
        e.g. 1-2-b/6-5-w/8-3-w/12-5-b/13-5-w/17-3-b/19-5-b/25-2-w w 0 0 0 0
        represents the starting position for backgammon game
        groups a-b-c mean: there are b checkers of c color on point an
        after all the a-b-c groups, there is a letter representing the current player
        turn, w for WHITE, b for BLACK. After the turn encoding, there are 2 groups of 2 numbers,
        first two numbers represent the number of barred pieces, first for white, then for black.
        Finally, the last 2 numbers represent the number of offloaded pieces for each player,
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
            starting_player: agent.Agent,
    ):
        """
        Function for starting a new fresh backgammon board
        given the starting agent
        """
        if starting_player.player == Player.WHITE:
            return cls.from_string(cls.STARTING_BOARD_SERIALIZED_STARTING_WHITE)
        return cls.from_string(cls.STARTING_BOARD_SERIALIZED_STARTING_BLACK)

    def is_empty_point(self, idx: int) -> bool:
        return self.__points[idx] == 0

    def is_point_of_color(self, idx: int, color: Player) -> bool:
        return (color == Player.WHITE and self.__points[idx] > 0) or (
                color == Player.BLACK and self.__points[idx] < 0
        )

    def all_checkers_in_home(self, pl: Player) -> bool:
        count_for_player = 0
        player_range = Player.get_home_board_range(pl)
        for idx in player_range:
            if self.__points[idx] > 0 and pl == Player.WHITE:
                count_for_player += self.num_checkers_at_index(idx)
            elif self.__points[idx] < 0 and pl == Player.BLACK:
                count_for_player += self.num_checkers_at_index(idx)

        count_for_player += self.__offed_black if pl == Player.BLACK else self.__offed_white
        return count_for_player == Board.INIT_CHECKER_COUNT

    def __eq__(self: "Board", ot: "Board") -> bool:
        return (
                self.points == ot.points
                and self.__turn == ot.turn
                and self.__barred_black == ot.__barred_black
                and self.__barred_white == ot.__barred_white
                and self.__offed_black == ot.__offed_black
                and self.__offed_white == ot.__offed_white
        )

    def __str__(self) -> str:
        return self.serialize_board()
