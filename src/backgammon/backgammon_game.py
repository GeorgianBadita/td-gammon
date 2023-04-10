from __future__ import annotations

import copy
import random
from collections import namedtuple
from enum import Enum
from typing import List, Optional, Set, Tuple, Dict, Any

import numpy as np

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

    def __repr__(self) -> str:
        return str(self.moves)


class GameState(Enum):
    NORMAL = 0
    BARRED_PIECES = 1
    BEAR_OFF = 2
    OVER = 3


class BackgammonGame:
    """
    Class for representing a backgammon game
    """

    TOKENS: Dict[Player, str] = {Player.WHITE: 'o', Player.BLACK: 'x'}
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
        self.__board = Board(
            points, turn, barred_white, barred_black, offed_white, offed_black
        )
        self.counter = 0

    @property
    def board(self) -> Board:
        return self.__board

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

    def get_features(self, pl: Player) -> List:
        """
        Function to compute the features as described in the td-gammon paper
        """
        features = []
        barred = self.__board.barred
        offed = self.__board.offed
        for player in [Player.WHITE, Player.BLACK]:
            for idx in range(self.__board.NUM_PLAYABLE_POINTS):
                point_features = [0.0] * 4
                if not self.__board.is_empty_point(idx) and self.__board.is_point_of_color(idx, player):
                    num_checkers = self.__board.num_checkers_at_index(idx)
                    if num_checkers == 1:
                        point_features[0] = 1.0
                    if num_checkers >= 2:
                        point_features[1] = 1.0
                    if num_checkers == 3:
                        point_features[2] = 1.0
                    if num_checkers >= 4:
                        point_features[3] = (num_checkers - 3) / 2
                features.extend(point_features)
        features.append(barred.white / 2.0)
        features.append(barred.black / 2.0)
        features.append(offed.white / Board.INIT_CHECKER_COUNT)
        features.append(offed.black / Board.INIT_CHECKER_COUNT)
        if pl == Player.WHITE:
            features.extend([1.0, 0.0])
        else:
            features.extend([0.0, 1.0])
        return np.array(features).reshape(1, -1)

    def step(self, mv: Optional[MoveRoll]) -> Tuple[List, int, bool, Dict[Any, Any]]:
        """
        Step function, compatible with OpenAI gym's model of the step function
        :return: (observation, reward, done, info)
        """
        if mv is not None:
            self.apply_move_roll(mv)

        # Getting the observation from the opponent's perspective as the current player is the one that just played
        observation = self.get_features(Player.BLACK if self.board.turn == Player.WHITE else Player.WHITE)
        reward = 0
        done = self.is_game_over
        info = {}

        if self.winner is not None or self.counter > 10_000:
            done = True
            reward = 1 if self.winner == Player.WHITE else 0
            info['winner'] = self.winner

        self.counter += 1

        return observation, reward, done, info

    def reset(self) -> Tuple[Player, Tuple[int, int], List]:
        """
        Reset the game to the starting position
        return: current player turn, first roll and initial observation
        """

        d1, d2 = self.roll_die()

        while d1 == d2:
            d1, d2 = self.roll_die()

        if d1 > d2:
            self.__board = Board.from_string(Board.STARTING_BOARD_SERIALIZED_STARTING_WHITE)
        else:
            self.__board = Board.from_string(Board.STARTING_BOARD_SERIALIZED_STARTING_BLACK)

        self.counter = 0

        return self.__board.turn, (d1, d2), self.get_features(self.__board.turn)

    def get_and_set_opponent_turn(self) -> Player:
        self.__board.turn = Player.WHITE if self.__board.turn == Player.BLACK else Player.BLACK
        return self.__board.turn

    def get_possible_move_rolls(self, die_roll: Tuple[int, int]) -> Set[MoveRoll]:
        move_rolls = set()
        r1, r2 = die_roll
        if r1 < r2:
            r1, r2 = r2, r1

        if r1 == r2:
            count = 4
            while not move_rolls and count > 0:
                self.__get_move_rolls(
                    tuple([r1] * count), [], move_rolls)
                count -= 1
        else:
            self.__get_move_rolls(
                (r1, r2), [], move_rolls)
            self.__get_move_rolls(
                (r2, r1), [], move_rolls)
            if not move_rolls:
                one_die_moves_r1 = self.__get_possible_moves_for_die(
                    r1)
                if one_die_moves_r1:
                    for move in one_die_moves_r1:
                        move_rolls.add(MoveRoll([move]))
                if not move_rolls:
                    one_die_moves_r2 = self.__get_possible_moves_for_die(
                        r2)
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
        return random.randint(1, 6), random.randint(1, 6)

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
        )

    @classmethod
    def new_game(
            cls: "BackgammonGame",
            # This is a bad design, that should be change
            # Only select a starting player when we use the .play() method
            # There is no point in even constructing the board at this point
            starting_player: Player = Player.WHITE,
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
        )

    def draw(self):
        """
        Function for drawing the board
        """
        points = [abs(x) for x in self.__board.points]
        bottom_board = points[:12][::-1]
        top_board = points[12:]
        colors = [self.TOKENS[Player.WHITE if x > 0 else Player.BLACK] for x in self.board.points]
        bottom_checkers_color = colors[:12][::-1]
        top_checkers_color = colors[12:]

        print("| 12 | 13 | 14 | 15 | 16 | 17 | BAR | 18 | 19 | 20 | 21 | 22 | 23 | OFF |")
        print(f"|--------Outer Board----------|     |-------P={self.TOKENS[Player.BLACK]} Home Board--------|     |")
        self.__print_half_board(top_board, top_checkers_color, Player.WHITE, rev=1)
        print("|-----------------------------|     |-----------------------------|     |")
        self.__print_half_board(bottom_board, bottom_checkers_color, Player.BLACK, rev=-1)
        print(f"|--------Outer Board----------|     |-------P={self.TOKENS[Player.WHITE]} Home Board--------|     |")
        print("| 11 | 10 |  9 |  8 |  7 |  6 | BAR |  5 |  4 |  3 |  2 |  1 |  0 | OFF |\n")

    def __print_half_board(self, half_board: List[int], colors: List[str], player: Player, rev: int = 1):
        token = self.TOKENS[player]
        offed = self.board.offed
        bar = self.board.barred
        off_player = offed.white if player == Player.WHITE else offed.black
        bar_player = bar.white if player == Player.WHITE else bar.black

        max_len = max([max(half_board), off_player, bar_player])
        for idx in range(max_len)[::rev]:
            row = [str(colors[k]) if half_board[k] > idx else " " for k in range(len(half_board))]
            bar = [f"{token} " if bar_player > idx else "  "]
            off = [f"{token} " if off_player > idx else "  "]
            row = row[:6] + bar + row[6:] + off
            print("|  " + " |  ".join(row) + " |")

    def __get_move_rolls(
            self,
            die_roll: Tuple,
            moves: List[Move],
            move_rolls: Set[MoveRoll]
    ):
        """
        Function for getting all possible move rolls for a given die roll
        """
        if len(die_roll) == 0 and moves:
            move_rolls.add(MoveRoll(moves))
            return

        d, d_rs = die_roll[0], die_roll[1:]
        moves_one_die = self.__get_possible_moves_for_die(d)
        for move in moves_one_die:
            self.__apply_move(move)
            self.__get_move_rolls(d_rs, moves + [move], move_rolls)
            self.__undo_move(move)

    def __get_possible_moves_for_die(self, die: int) -> Set[Move]:
        moves = set()
        if self.game_state_for_current_turn == GameState.NORMAL:
            direction = 1
            if self.__board.turn == Player.WHITE:
                direction = -1
            moves.update(self.__get_normal_moves_for_die(0, Board.NUM_PLAYABLE_POINTS, direction, die))
        elif self.game_state_for_current_turn == GameState.BARRED_PIECES:
            if self.__board.turn == Player.WHITE:
                checker_num = self.__board.num_checkers_at_index(Board.NUM_PLAYABLE_POINTS - die)
                # If the destination is of the moving player's color or empty
                if self.__board.is_point_of_color(Board.NUM_PLAYABLE_POINTS - die, self.__board.turn) or \
                        checker_num == 0:
                    # Make a normal bar entry move
                    moves.add(Move(-1, Board.NUM_PLAYABLE_POINTS - die, MoveType.BAR_ENTRY))
                elif not self.__board.is_point_of_color(Board.NUM_PLAYABLE_POINTS - die, self.__board.turn) and \
                        checker_num == 1:
                    # Make a normal bar entry move that also puts one of the opponent's checkers on the bar
                    moves.add(Move(-1, Board.NUM_PLAYABLE_POINTS - die, MoveType.BAR_ENTRY_PUT_ON_BAR))
            else:
                checker_num = self.__board.num_checkers_at_index(die - 1)
                # If the destination is of the moving player's color or empty
                if self.__board.is_point_of_color(die - 1, self.__board.turn) or \
                        checker_num == 0:
                    # Make a normal bar entry move
                    moves.add(Move(-1, die - 1, MoveType.BAR_ENTRY))
                elif not self.__board.is_point_of_color(die - 1, self.__board.turn) and \
                        checker_num == 1:
                    # Make a normal bar entry move that also puts one of the opponent's checkers on the bar
                    moves.add(Move(-1, die - 1, MoveType.BAR_ENTRY_PUT_ON_BAR))
        elif self.game_state_for_current_turn == GameState.BEAR_OFF:
            direction = 1
            if self.__board.turn == Player.WHITE:
                direction = -1
                moves.update(self.__get_normal_moves_for_die(0, 6, direction, die))
                index_of_last_checker = 5
                while index_of_last_checker >= 0 >= self.__board.points[index_of_last_checker]:
                    index_of_last_checker -= 1
                if die >= index_of_last_checker + 1:
                    moves.add(Move(index_of_last_checker, -1, MoveType.BEAR_OFF))
                if self.__board.points[die - 1] > 0:
                    moves.add(Move(die - 1, -1, MoveType.BEAR_OFF))
            else:
                moves.update(self.__get_normal_moves_for_die(18, Board.NUM_PLAYABLE_POINTS, direction, die))
                index_of_last_checker = 18
                while index_of_last_checker < Board.NUM_PLAYABLE_POINTS and \
                        self.__board.points[index_of_last_checker] >= 0:
                    index_of_last_checker += 1
                if die >= Board.NUM_PLAYABLE_POINTS - index_of_last_checker:
                    moves.add(Move(index_of_last_checker, -1, MoveType.BEAR_OFF))
                if self.__board.points[Board.NUM_PLAYABLE_POINTS - die] < 0:
                    moves.add(Move(Board.NUM_PLAYABLE_POINTS - die, -1, MoveType.BEAR_OFF))
        return moves

    def __get_normal_moves_for_die(self, start: int, end: int, direction: int, die: int) -> List[Move]:
        moves = []
        for idx in range(start, end):
            # Check if the starting point is of the moving player's color
            # And there is at least one checker to move
            if self.__board.is_point_of_color(idx, self.__board.turn) and self.__board.num_checkers_at_index(
                    idx) > 0:
                dest_idx = idx + (die * direction)
                # If the destination is on the board
                if self.__is_destination_valid(dest_idx):
                    # If the destination is of the moving player's color or empty
                    if self.__board.is_point_of_color(dest_idx, self.__board.turn) or \
                            self.__board.num_checkers_at_index(dest_idx) == 0:
                        # Make a normal move
                        moves.append(Move(idx, dest_idx, MoveType.NORMAL))
                    # If the destination is of the opponent's color
                    elif not self.__board.is_point_of_color(dest_idx, self.__board.turn) and \
                            self.__board.num_checkers_at_index(dest_idx) == 1:
                        # Make a normal moves that also puts one of the opponent's checkers on the bar
                        moves.append(Move(idx, dest_idx, MoveType.NORMAL_PUT_ON_BAR))
        return moves

    def __is_destination_valid(self, idx) -> bool:
        return 0 <= idx < Board.NUM_PLAYABLE_POINTS

    def __apply_move(self, mv: Move):
        """
        Function for applying a move
        """
        from_point, to_point = mv.from_point, mv.to_point

        if mv.move_type == MoveType.NORMAL:
            if self.__board.is_point_of_color(from_point, Player.WHITE):
                # Remove the white checker from the source
                self.__board.dec_point(from_point)
                # Add the white checker to the destination
                self.__board.inc_point(to_point)
            else:
                # Remove the black checker from the source
                self.__board.inc_point(from_point)
                # Add the black checker to the destination
                self.__board.dec_point(to_point)
        elif mv.move_type == MoveType.BEAR_OFF:
            if self.__board.is_point_of_color(from_point, Player.WHITE):
                # Remove the white checker from the source
                self.__board.dec_point(from_point)
                # Add the white checker to the off
                self.__board.inc_offed(Player.WHITE)
            else:
                # Remove the black checker from the source
                self.__board.inc_point(from_point)
                # Add the black checker to the off
                self.__board.inc_offed(Player.BLACK)
        elif mv.move_type == MoveType.BAR_ENTRY:
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
        elif mv.move_type == MoveType.NORMAL_PUT_ON_BAR:
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
        elif mv.move_type == MoveType.BAR_ENTRY_PUT_ON_BAR:
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

        # TODO: remove this once piece invariant bugs are solved
        # self.__assert_checkers_invariant()

    def __undo_move(self, mv: Move):
        """
        Function for undoing a move
        """
        from_point, to_point = mv.from_point, mv.to_point
        if mv.move_type == MoveType.NORMAL:
            if self.__board.is_point_of_color(to_point, Player.WHITE):
                self.__board.inc_point(from_point)
                self.__board.dec_point(to_point)
            else:
                self.__board.dec_point(from_point)
                self.__board.inc_point(to_point)
        elif mv.move_type == MoveType.BEAR_OFF:
            if self.__board.index_in_home(from_point, Player.WHITE):
                self.__board.inc_point(from_point)
                self.__board.dec_offed(Player.WHITE)
            elif self.__board.index_in_home(from_point, Player.BLACK):
                self.__board.dec_point(from_point)
                self.__board.dec_offed(Player.BLACK)
            else:
                raise ValueError(
                    "Bear off move from point not in either player home")
        elif mv.move_type == MoveType.NORMAL_PUT_ON_BAR:
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
        elif mv.move_type == MoveType.BAR_ENTRY_PUT_ON_BAR:
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
        elif mv.move_type == MoveType.BAR_ENTRY:
            if self.__board.is_point_of_color(to_point, Player.WHITE):
                # Remove the white checker from the destination point
                self.__board.dec_point(to_point)
                # Add the white checker to the bar
                self.__board.inc_barred(Player.WHITE)
            else:
                # Remove the black checker from the destination point
                self.__board.inc_point(to_point)
                # Add the black checker to the bar
                self.__board.inc_barred(Player.BLACK)
        # TODO: remove this once piece invariant bugs are solved
        # self.__assert_checkers_invariant()

    def __assert_checkers_invariant(self):
        # Checks that there are always 30 pieces in the game (board + barred + offed)
        num = 0
        offed = self.__board.offed
        barred = self.__board.barred
        for idx in range(Board.NUM_PLAYABLE_POINTS):
            num += self.__board.num_checkers_at_index(idx)
        total = num + barred.white + barred.black + offed.white + offed.black
        assert total == 30, f"Piece invariant violated, {total} instead of 30 checkers"

    def __all_pieces_in_house_for_turn(self) -> bool:
        """
        Returns true if all the pieces of the player whose turn it is are in their home
        """
        if self.__board.turn == Player.WHITE:
            return self.__board.all_checkers_in_home(Player.WHITE)
        else:
            return self.__board.all_checkers_in_home(Player.BLACK)

    def __eq__(self: "BackgammonGame", ot: "BackgammonGame") -> bool:
        return self.__board == ot.board
