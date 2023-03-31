from __future__ import annotations

import copy
import random
from collections import namedtuple
from enum import Enum
from typing import List, Optional, Set, Tuple

from src.backgammon.agent import agent
from src.backgammon.board import Board, Player


class MoveType(Enum):
    # Normal move of checker from point x to y
    NORMAL = 0
    # Move of checker from point x to y, AND barring one of
    # the opponent pieces in the process
    NORMAL_PUT_ON_BAR = 1
    # Normal bar entry
    BAR_ENTRY = 2
    # Bar entry AND barring one of the opponent pieces in the process
    BAR_ENTRY_PUT_ON_BAR = 3
    # Normal bear off move
    BEAR_OFF = 4


Move = namedtuple("Move", "from_point to_point move_type")


class MoveRoll:
    def __init__(self, moves: List[Move]):
        self.__moves = moves

    @property
    def moves(self) -> List[Move]:
        return self.__moves


class GameState(Enum):
    NORMAL = 0
    BARRED_PIECES = 1
    BEAR_OFF = 2
    OVER = 3


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
    ):
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

    @property
    def is_game_over(self) -> bool:
        offed = self.board.offed
        return (
                offed.black == Board.INIT_CHECKER_COUNT
                or offed.white == Board.INIT_CHECKER_COUNT
        )

    @property
    def winner(self) -> Optional[Player]:
        offed = self.board.offed
        if offed.black == Board.INIT_CHECKER_COUNT:
            return Player.BLACK
        elif offed.white == Board.INIT_CHECKER_COUNT:
            return Player.WHITE
        return None

    @property
    def game_state_for_current_turn(self) -> GameState:
        barred = self.board.barred
        if self.is_game_over:
            return GameState.OVER
        if (self.__board.turn == Player.WHITE and barred.white > 0) or (
                self.__board.turn == Player.BLACK and barred.black > 0
        ):
            return GameState.BARRED_PIECES
        if self.__all_pieces_in_house_for_turn():
            return GameState.BEAR_OFF
        return GameState.NORMAL

    def play(self) -> Player:
        """
        Function that plays a game until it finishes
        """
        while not self.is_game_over:
            self.play_turn()
            self.board.turn = (
                Player.WHITE if self.__board.turn == Player.BLACK else Player.BLACK
            )

        winner = self.winner
        if winner is None:
            raise ValueError(
                "Something is wrong, game needed without a winner, winner is None"
            )
        return winner

    def play_turn(self):
        die_roll = self.roll_die()
        move_rolls = self.get_possible_move_rolls(die_roll)

        if self.board.turn == Player.WHITE:
            selected_move = self.__white_player_agent.get_move(move_rolls)
        else:
            selected_move = self.__black_player_agent.get_move(move_rolls)

        self.apply_move_roll(selected_move)

    def get_possible_move_rolls(self, die_roll: Tuple[int, int]) -> Set[MoveRoll]:
        move_rolls = set()
        r1, r2 = die_roll
        if r1 < r2:
            r2, r1 = r1, r2

        if r1 == r2:
            count = 4
            while not move_rolls and count > 0:
                self.__get_move_rolls(
                    tuple([r1] * count), None, move_rolls, self.__board.turn)
                count -= 1
        else:
            self.__get_move_rolls(
                die_roll, None, move_rolls, self.__board.turn)
            self.__get_move_rolls(
                (r2, r1), None, move_rolls, self.__board.turn)
            if not move_rolls:
                one_die_moves_r1 = self.__get_possible_moves_for_die(
                    r1, self.__board.turn)
                if one_die_moves_r1:
                    for move in one_die_moves_r1:
                        move_rolls.add(MoveRoll([move]))
                if not move_rolls:
                    one_die_moves_r2 = self.__get_possible_moves_for_die(
                        r2, self.__board.turn)
                    if one_die_moves_r2:
                        for move in one_die_moves_r2:
                            move_rolls.add(MoveRoll([move]))

        return move_rolls

    def apply_move_roll(self, mv: Optional[MoveRoll]):
        if mv is None:
            return

        for mv in mv.moves:
            self.__apply_move(mv)

    def undo_move_roll(self, mv_roll: Optional[MoveRoll]):
        """
        Think more about undo move roll as it is not so easy
        """
        if mv_roll is None:
            return

        for mv in reversed(mv_roll.moves):
            self.__undo_move(mv)

    def roll_die(self) -> Tuple[int, int]:
        return random.randint(0, 6), random.randint(0, 6)

    def clone(self) -> "BackgammonGame":
        point_copy = copy.deepcopy(self.board.points)
        barred = self.board.barred
        offed = self.board.offed
        return BackgammonGame(
            point_copy,
            self.__board.turn,
            barred.white,
            barred.black,
            offed.white,
            offed.white,
            self.__white_player_agent,
            self.__black_player_agent
        )

    @classmethod
    def new_game(
            cls: "BackgammonGame",
            white_agent: agent.Agent,
            black_agent: agent.Agent,
            starting_player: object = Player.WHITE,
    ) -> "BackgammonGame":
        """
        Function for starting a new fresh backgammon game
        given the starting agents
        """
        if starting_player == Player.WHITE:
            board = Board.from_string(
                Board.STARTING_BOARD_SERIALIZED_STARTING_WHITE)
        else:
            board = Board.from_string(
                Board.STARTING_BOARD_SERIALIZED_STARTING_BLACK)

        return BackgammonGame(
            board.points,
            board.turn,
            board.barred.white,
            board.barred.black,
            board.offed.white,
            board.offed.black,
            white_agent,
            black_agent,
        )

    def __get_move_rolls(
            self,
            die_roll: Tuple,
            move_roll: Optional[MoveRoll],
            move_rolls: Set[MoveRoll],
            turn: Player,
    ):
        """
        Function for getting all possible move rolls for a given die roll
        """
        if len(die_roll) == 0 and move_roll is not None:
            move_rolls.add(move_roll)
            return

    def __get_possible_moves_for_die(self, die: int, turn: Player) -> List[Move]:
        return []

    def __apply_move(self, mv: Move):
        """
        Function for applying a move
        """
        from_point, to_point = mv.from_point, mv.to_point
        match mv.move_type:
            case MoveType.NORMAL:
                if self.__board.is_point_of_color(from_point, Player.WHITE):
                    # Remove the white checker from the source
                    self.__board.dec_point(from_point)
                    # Add the white checker to the destination
                    self.__board.inc_point(to_point)
                else:
                    # Remove the black checker from the source
                    self.__board.inc_barred(from_point)
                    # Add the black checker to the destination
                    self.__board.dec_barred(to_point)
            case MoveType.BEAR_OFF:
                if self.__board.is_point_of_color(from_point, Player.WHITE):
                    # Remove the white checker from the source
                    self.__board.dec_point(from_point)
                    # Add the white checker to the off
                    self.__board.inc_offed(Player.WHITE)
                else:
                    # Remove the black checker from the source
                    self.__board.inc_barred(from_point)
                    # Add the black checker to the off
                    self.__board.inc_offed(Player.BLACK)
            case MoveType.BAR_ENTRY:
                if self.__board.index_in_home(to_point, Player.BLACK):
                    # Remove the white piece from the bar
                    self.__board.dec_barred(Player.WHITE)
                    # Add the white piece to the board
                    self.__board.inc_point(to_point)
                else:
                    # Remove the black piece from the bar
                    self.__board.dec_barred(Player.BLACK)
                    # Add the black piece to the board
                    self.__board.dec_point(to_point)
            case MoveType.NORMAL_PUT_ON_BAR:
                if self.__board.is_point_of_color(from_point, Player.WHITE):
                    # Remove the white checker from the source
                    self.__board.dec_point(from_point)
                    # Add the white checker to the destination
                    self.__board.inc_point(to_point)
                    # Remove the black checker from the destination
                    self.__board.inc_point(to_point)
                    # Add the black checker to the bar
                    self.__board.inc_barred(Player.BLACK)
                else:
                    # Remove the black checker from the source
                    self.__board.inc_point(from_point)
                    # Add the black checker to the destination
                    self.__board.dec_point(to_point)
                    # Remove the white checker from the destination
                    self.__board.dec_point(to_point)
                    # Add the white checker to the bar
                    self.__board.inc_barred(Player.WHITE)
            case MoveType.BAR_ENTRY_PUT_ON_BAR:
                if self.__board.index_in_home(to_point, Player.BLACK):
                    # Put the white piece on the board
                    self.__board.inc_point(to_point)
                    # Remove the white piece from the bar
                    self.__board.dec_barred(Player.WHITE)
                    # Remove the black piece from the board
                    self.__board.inc_point(to_point)
                    # Add the black piece to the bar
                    self.__board.inc_barred(Player.BLACK)
                else:
                    # Put the black piece on the board
                    self.__board.dec_point(to_point)
                    # Remove the black piece from the bar
                    self.__board.dec_barred(Player.BLACK)
                    # Remove the white piece from the board
                    self.__board.dec_point(to_point)
                    # Add the white piece to the bar
                    self.__board.inc_barred(Player.WHITE)

    def __undo_move(self, mv: Move):
        """
        Function for undoing a move
        """
        from_point, to_point = mv.from_point, mv.to_point
        match mv.move_type:
            case MoveType.NORMAL:
                if self.__board.is_point_of_color(to_point, Player.WHITE):
                    self.__board.inc_point(from_point)
                    self.__board.dec_point(to_point)
                else:
                    self.__board.dec_point(from_point)
                    self.__board.inc_point(to_point)
            case MoveType.BEAR_OFF:
                if self.__board.index_in_home(from_point, Player.WHITE):
                    self.__board.inc_point(from_point)
                    self.__board.dec_offed(Player.WHITE)
                elif self.__board.index_in_home(from_point, Player.BLACK):
                    self.__board.dec_point(from_point)
                    self.__board.dec_offed(Player.BLACK)
                else:
                    raise ValueError(
                        "Bear off move from point not in either player home")
            case MoveType.NORMAL_PUT_ON_BAR:
                if self.__board.is_point_of_color(to_point, Player.WHITE):
                    # Put the white checker back
                    self.__board.inc_point(from_point)
                    # Remove the white checker from destination
                    self.__board.dec_point(to_point)
                    # Add the black checker back on the destination
                    self.__board.dec_point(to_point)
                    # Remove the black checker from the bar
                    self.__board.dec_barred(Player.BLACK)
                else:
                    # Put the black checker back
                    self.__board.dec_point(from_point)
                    # Remove the black checker from destination
                    self.__board.inc_point(to_point)
                    # Add the white checker back on the destination
                    self.__board.inc_point(to_point)
                    # Remove the white checker from the bar
                    self.__board.dec_barred(Player.WHITE)
            case MoveType.BAR_ENTRY_PUT_ON_BAR:
                if self.__board.is_point_of_color(to_point, Player.WHITE):
                    # Remove the white checker from the destination point
                    self.__board.dec_point(to_point)
                    # Add the black checker back on the destination
                    self.__board.dec_point(to_point)
                    # Remove the black checker from the bar
                    self.__board.dec_barred(Player.BLACK)
                    # Add the white checker back on the bar
                    self.__board.inc_barred(Player.WHITE)
                else:
                    # Remove the black checker from the destination point
                    self.__board.inc_point(to_point)
                    # Add the white checker back on the destination
                    self.__board.inc_point(to_point)
                    # Remove the white checker from the bar
                    self.__board.dec_barred(Player.WHITE)
                    # Add the black checker back on the bar
                    self.__board.inc_barred(Player.BLACK)
            case MoveType.BAR_ENTRY:
                if self.__board.is_point_of_color(to_point, Player.WHITE):
                    # Remove the black checker from the destination point
                    self.__board.inc_point(to_point)
                    # Add the black checker to the bar
                    self.__board.inc_barred(Player.BLACK)
                else:
                    # Remove the white checker from the destination point
                    self.__board.dec_point(to_point)
                    # Add the white checker to the bar
                    self.__board.inc_barred(Player.WHITE)

    def __all_pieces_in_house_for_turn(self) -> bool:
        """
        Returns true if all the pieces of the player whose turn it is are in their home
        """
        if self.__board.turn == Player.WHITE:
            return self.__board.all_pieces_in_home(Player.WHITE)
        else:
            return self.__board.all_pieces_in_home(Player.BLACK)

    def __eq__(self: "BackgammonGame", ot: "BackgammonGame") -> bool:
        return (
                self.__board == ot.board
                and self.__white_player_agent == ot.white_player_agent
                and self.__black_player_agent == ot.black_player_agent
        )
