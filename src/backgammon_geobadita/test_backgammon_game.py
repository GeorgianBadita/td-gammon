import unittest
from typing import Tuple, List, Optional

from parameterized import parameterized

from src.backgammon_geobadita.backgammon_game import BackgammonGame, GameState, MoveRoll, Move, MoveType
from src.backgammon_geobadita.board import Player, Board


def make_compute_game_state_test_data() -> List[Tuple[str, BackgammonGame, GameState]]:
    # Test 1, expect beginning of game to have GamesState.NORMAL
    game = BackgammonGame.new_game(starting_player=Player.WHITE)
    expected_game_state = GameState.NORMAL

    # Test 2, expect game state to be GameState.BARRED_PIECES when white has barred pieces
    game2 = game.clone()
    game2.board.points[5] -= 1
    game2.board.inc_barred(Player.WHITE)
    expected_game_state2 = GameState.BARRED_PIECES

    # Test 3, expect game state to be GameState.BARRED_PIECES when black has barred pieces
    game3 = game.clone()
    game3.board.turn = Player.BLACK
    game3.board.points[23] += 1
    game3.board.inc_barred(Player.BLACK)
    expected_game_state3 = GameState.BARRED_PIECES

    # Test 4, expect game state to be GameState.NORMAL when white has barred pieces, but it's black's turn
    game4 = game.clone()
    game4.board.turn = Player.BLACK
    game2.board.points[5] -= 1
    game2.board.inc_barred(Player.WHITE)
    expected_game_state4 = GameState.NORMAL

    # Test 5, expect game state to be GameState.BEAR_OFF when white has all pieces in home
    game5 = game.clone()
    game5.board.points[7] = 0
    game5.board.points[12] = 0
    game5.board.points[23] = 0
    game5.board.points[4] = 10
    expected_game_state5 = GameState.BEAR_OFF

    # Test 6, expect game state to be GameState.OVER when black has all pieces offed
    game6 = game.clone()
    game6.board.points[0] = 0
    game6.board.points[11] = 0
    game6.board.points[16] = 0
    game6.board.points[18] = 0
    # I know this is unnecessarily ugly, but I am too lazy to change it right now
    list(map((lambda _: game6.board.inc_offed(Player.WHITE)), range(15)))
    expected_game_state6 = GameState.OVER

    return [('beginning_of_game_is_normal_state', game, expected_game_state),
            ('white_has_barred_pieces_state_is_barred', game2, expected_game_state2),
            ('black_has_barred_pieces_state_is_barred', game3, expected_game_state3),
            ('white_has_barred_pieces_but_turn_is_black_state_is_normal', game4, expected_game_state4),
            ('white_has_all_pieces_in_home_state_is_bear_off', game5, expected_game_state5),
            ('black_has_all_pieces_in_offed_state_is_over', game6, expected_game_state6)]


def make_apply_normal_moves_test_data() -> List[Tuple[str, BackgammonGame, Optional[MoveRoll], BackgammonGame]]:
    # Test 1, expect no move roll provided, nothing happens
    game = BackgammonGame.new_game(starting_player=Player.WHITE)
    expected_game = game.clone()

    # Test 2, apply 6 points move from white at the beginning of the game
    game2 = game.clone()
    move_roll2 = MoveRoll([Move(from_point=23, to_point=17, move_type=MoveType.NORMAL)])
    expected_game2 = game2.clone()
    expected_game2.board.points[Board.NUM_PLAYABLE_POINTS - 1] -= 1
    expected_game2.board.points[Board.NUM_PLAYABLE_POINTS - 1 - 6] += 1

    # Test 3, apply 6 points move from black at the beginning of the game
    game3 = game.clone()
    game3.board.turn = Player.BLACK
    move_roll3 = MoveRoll([Move(from_point=11, to_point=17, move_type=MoveType.NORMAL)])
    expected_game3 = game3.clone()
    expected_game3.board.points[11] += 1
    expected_game3.board.points[17] -= 1

    # Test 4, apply two moves, a 3 and a 1 from white's perspective at the beginning of the game
    game4 = game.clone()
    move_roll4 = MoveRoll([Move(from_point=7, to_point=4, move_type=MoveType.NORMAL),
                           Move(from_point=5, to_point=4, move_type=MoveType.NORMAL)])
    expected_game4 = game4.clone()
    expected_game4.board.points[7] -= 1
    expected_game4.board.points[5] -= 1
    expected_game4.board.points[4] = 2

    # Test 5, apply four moves of 6 at the beginning of the game for black
    game5 = game.clone()
    game5.board.turn = Player.BLACK
    move_roll5 = MoveRoll([Move(from_point=11, to_point=17, move_type=MoveType.NORMAL)] * 4)
    expected_game5 = game5.clone()
    expected_game5.board.points[11] = -1
    expected_game5.board.points[17] = -4

    # Test 6, apply a move that bars one of black's pieces
    game6 = game.clone()
    game6.board.points[17] = -1
    game6.board.points[16] += 1
    move_roll6 = MoveRoll([Move(from_point=23, to_point=17, move_type=MoveType.NORMAL_PUT_ON_BAR)])
    expected_game6 = game6.clone()
    expected_game6.board.inc_barred(Player.BLACK)
    expected_game6.board.points[17] = 1
    expected_game6.board.points[23] -= 1

    # Test 7, apply a move that bars one of white's pieces
    game7 = game.clone()
    game7.board.turn = Player.BLACK
    game7.board.points[6] = 1
    game7.board.points[7] -= 1
    move_roll7 = MoveRoll([Move(from_point=0, to_point=6, move_type=MoveType.NORMAL_PUT_ON_BAR)])
    expected_game7 = game7.clone()
    expected_game7.board.inc_barred(Player.WHITE)
    expected_game7.board.points[6] = -1
    expected_game7.board.points[0] += 1

    return [('no_move_roll_provided_nothing_happens', game, None, expected_game),
            ('white_move_6_beginning_of_game', game2, move_roll2, expected_game2),
            ('black_move_6_beginning_of_game', game3, move_roll3, expected_game3),
            ('white_move_of_3_and_1_at_the_beginning_of_the_game', game4, move_roll4, expected_game4),
            ('black_move_of_6_four_times_at_the_beginning_of_the_game', game5, move_roll5, expected_game5),
            ('white_move_bars_one_black_checker', game6, move_roll6, expected_game6),
            ('black_move_bars_one_white_checker', game7, move_roll7, expected_game7)]


def make_checker_on_bar_moves_test_data() -> List[Tuple[str, BackgammonGame, Optional[MoveRoll], BackgammonGame]]:
    # Test 1, black has a piece on bar
    game = BackgammonGame.new_game(starting_player=Player.WHITE)
    game1 = game.clone()
    game1.board.turn = Player.BLACK
    game1.board.points[16] += 1
    game1.board.inc_barred(Player.BLACK)
    move_roll = MoveRoll([Move(from_point=-1, to_point=0, move_type=MoveType.BAR_ENTRY)])
    expected_game1 = game1.clone()
    expected_game1.board.points[0] -= 1
    expected_game1.board.dec_barred(Player.BLACK)

    # Test 2, white has 2 pieces on bar
    game2 = game.clone()
    game2.board.points[5] = 3
    game2.board.inc_barred(Player.WHITE)
    game2.board.inc_barred(Player.WHITE)
    move_roll2 = MoveRoll([Move(from_point=-1, to_point=22, move_type=MoveType.BAR_ENTRY)])
    expected_game2 = game2.clone()
    expected_game2.board.points[22] = 1
    expected_game2.board.dec_barred(Player.WHITE)

    # Test 3, white has 2 pieces on bar, enters with one and bars black's piece
    game3 = game.clone()
    game3.board.points[5] = 3
    game3.board.inc_barred(Player.WHITE)
    game3.board.inc_barred(Player.WHITE)
    game3.board.points[22] = -1
    game3.board.points[16] += 1
    move_roll3 = MoveRoll([Move(from_point=-1, to_point=22, move_type=MoveType.BAR_ENTRY_PUT_ON_BAR)])
    expected_game3 = game3.clone()
    expected_game3.board.points[22] = 1
    expected_game3.board.dec_barred(Player.WHITE)
    expected_game3.board.inc_barred(Player.BLACK)

    # Test 4, black has 2 pieces on bar, enters with one and bars white's piece
    game4 = game.clone()
    game4.board.points[18] = -3
    game4.board.inc_barred(Player.BLACK)
    game4.board.inc_barred(Player.BLACK)
    game4.board.points[3] = 1
    game4.board.points[7] -= 1
    move_roll4 = MoveRoll([Move(from_point=-1, to_point=3, move_type=MoveType.BAR_ENTRY_PUT_ON_BAR)])
    expected_game4 = game4.clone()
    expected_game4.board.points[3] = -1
    expected_game4.board.inc_barred(Player.WHITE)
    expected_game4.board.dec_barred(Player.BLACK)

    return [('black_has_a_checker_on_bar', game1, move_roll, expected_game1),
            ('white_has_two_checkers_on_bar', game2, move_roll2, expected_game2),
            ('white_has_two_checkers_on_bar_bars_black', game3, move_roll3, expected_game3),
            ('black_has_two_checkers_on_bar_bars_white', game4, move_roll4, expected_game4)]


def make_bear_off_moves_test_data() -> List[Tuple[str, BackgammonGame, Optional[MoveRoll], BackgammonGame]]:
    # Test 1, black bears off 1 checker
    game = BackgammonGame.new_game(starting_player=Player.WHITE)
    game1 = game.clone()
    game1.board.turn = Player.BLACK
    game1.board.points[22] = -7
    game1.board.points[19] = -3
    game1.board.points[16] = 0
    game1.board.points[11] = 0
    game1.board.points[0] = 0
    move_roll1 = MoveRoll([Move(from_point=22, to_point=-1, move_type=MoveType.BEAR_OFF)])
    expected_board1 = game1.clone()
    expected_board1.board.points[22] = -6
    expected_board1.board.inc_offed(Player.BLACK)

    # Test 2, white bears off 1 checker
    game2 = game.clone()
    game2.board.points[1] = 7
    game2.board.points[4] = 3
    game2.board.points[7] = 0
    game2.board.points[12] = 0
    game2.board.points[23] = 0
    move_roll2 = MoveRoll([Move(from_point=4, to_point=-1, move_type=MoveType.BEAR_OFF)])
    expected_board2 = game2.clone()
    expected_board2.board.points[4] = 2
    expected_board2.board.inc_offed(Player.WHITE)

    return [('black_bears_off_1_checker', game1, move_roll1, expected_board1),
            ('white_bears_off_1_checker', game2, move_roll2, expected_board2)]


def make_valid_moves_test_data() -> List[Tuple[str, BackgammonGame, Tuple[int, int], List[MoveRoll]]]:
    # Test 1, test all valid moves from start position, white to move
    # Die roll is (1, 2)
    game1 = BackgammonGame.new_game(starting_player=Player.WHITE)
    die_roll1 = (1, 2)
    expected_move_rolls1 = [
        MoveRoll([Move(from_point=23, to_point=21, move_type=MoveType.NORMAL),
                  Move(from_point=21, to_point=20, move_type=MoveType.NORMAL)]),
        MoveRoll([Move(from_point=23, to_point=21, move_type=MoveType.NORMAL),
                  Move(from_point=23, to_point=22, move_type=MoveType.NORMAL)]),
        MoveRoll([Move(from_point=5, to_point=3, move_type=MoveType.NORMAL),
                  Move(from_point=3, to_point=2, move_type=MoveType.NORMAL)]),
        MoveRoll([Move(from_point=5, to_point=3, move_type=MoveType.NORMAL),
                  Move(from_point=5, to_point=4, move_type=MoveType.NORMAL)]),
        MoveRoll([Move(from_point=7, to_point=6, move_type=MoveType.NORMAL),
                  Move(from_point=5, to_point=3, move_type=MoveType.NORMAL)]),
        MoveRoll([Move(from_point=23, to_point=22, move_type=MoveType.NORMAL),
                  Move(from_point=5, to_point=3, move_type=MoveType.NORMAL)]),
        MoveRoll([Move(from_point=5, to_point=4, move_type=MoveType.NORMAL),
                  Move(from_point=7, to_point=5, move_type=MoveType.NORMAL)]),
        MoveRoll([Move(from_point=7, to_point=6, move_type=MoveType.NORMAL),
                  Move(from_point=7, to_point=5, move_type=MoveType.NORMAL)]),
        MoveRoll([Move(from_point=23, to_point=22, move_type=MoveType.NORMAL),
                  Move(from_point=7, to_point=5, move_type=MoveType.NORMAL)]),
        MoveRoll([Move(from_point=12, to_point=10, move_type=MoveType.NORMAL),
                  Move(from_point=5, to_point=4, move_type=MoveType.NORMAL)]),
        MoveRoll([Move(from_point=12, to_point=10, move_type=MoveType.NORMAL),
                  Move(from_point=7, to_point=6, move_type=MoveType.NORMAL)]),
        MoveRoll([Move(from_point=12, to_point=10, move_type=MoveType.NORMAL),
                  Move(from_point=10, to_point=9, move_type=MoveType.NORMAL)]),
        MoveRoll([Move(from_point=23, to_point=22, move_type=MoveType.NORMAL),
                  Move(from_point=12, to_point=10, move_type=MoveType.NORMAL)]),
        MoveRoll([Move(from_point=23, to_point=21, move_type=MoveType.NORMAL),
                  Move(from_point=5, to_point=4, move_type=MoveType.NORMAL)]),
        MoveRoll([Move(from_point=23, to_point=21, move_type=MoveType.NORMAL),
                  Move(from_point=7, to_point=6, move_type=MoveType.NORMAL)]),
    ]

    # Test 2, test all valid moves from start position, black to move
    # Die roll is (6, 5)
    game2 = game1.clone()
    game2.board.turn = Player.BLACK
    die_roll2 = (6, 5)
    expected_move_rolls2 = [
        MoveRoll([Move(from_point=0, to_point=6, move_type=MoveType.NORMAL),
                  Move(from_point=6, to_point=11, move_type=MoveType.NORMAL)]),
        MoveRoll([Move(from_point=0, to_point=6, move_type=MoveType.NORMAL),
                  Move(from_point=11, to_point=16, move_type=MoveType.NORMAL)]),
        MoveRoll([Move(from_point=0, to_point=6, move_type=MoveType.NORMAL),
                  Move(from_point=16, to_point=21, move_type=MoveType.NORMAL)]),
        MoveRoll([Move(from_point=11, to_point=17, move_type=MoveType.NORMAL),
                  Move(from_point=11, to_point=16, move_type=MoveType.NORMAL)]),
        MoveRoll([Move(from_point=11, to_point=17, move_type=MoveType.NORMAL),
                  Move(from_point=16, to_point=21, move_type=MoveType.NORMAL)]),
        MoveRoll([Move(from_point=11, to_point=17, move_type=MoveType.NORMAL),
                  Move(from_point=17, to_point=22, move_type=MoveType.NORMAL)]),
        MoveRoll([Move(from_point=11, to_point=16, move_type=MoveType.NORMAL),
                  Move(from_point=16, to_point=22, move_type=MoveType.NORMAL)]),
        MoveRoll([Move(from_point=16, to_point=22, move_type=MoveType.NORMAL),
                  Move(from_point=16, to_point=21, move_type=MoveType.NORMAL)]),
    ]

    # Test 3, test where no moves are possible, white to move
    # Die roll is (1, 3)
    game3 = game1.clone()
    game3.board.points[23] = 0
    game3.board.points[12] = 0
    game3.board.points[7] = 0
    game3.board.points[5] = 0
    game3.board.points[19] = 1
    die_roll3 = (1, 3)
    expected_move_rolls3 = []

    # Test 4, test bear off at the end of the game, white to move
    # Die roll is (2, 3)
    game4 = game1.clone()
    game4.board.points[23] = 0
    game4.board.points[12] = 0
    game4.board.points[7] = 0
    game4.board.points[5] = 0
    game4.board.points[1] = 7
    game4.board.points[2] = 8
    die_roll4 = (2, 3)
    expected_move_rolls4 = [
        MoveRoll([Move(from_point=1, to_point=-1, move_type=MoveType.BEAR_OFF),
                  Move(from_point=2, to_point=-1, move_type=MoveType.BEAR_OFF)]),
        MoveRoll([Move(from_point=2, to_point=-1, move_type=MoveType.BEAR_OFF),
                  Move(from_point=1, to_point=-1, move_type=MoveType.BEAR_OFF)]),
    ]

    # Test 5, test bearing off at the end of the game, black to move with normal moves possible
    # Die roll is (5, 6)
    game5 = game1.clone()
    game5.board.turn = Player.BLACK
    game5.board.points[0] = 0
    game5.board.points[11] = 0
    game5.board.points[16] = 0
    game5.board.points[23] = 0
    game5.board.points[6] = 2
    game5.board.points[23] = -10
    die_roll5 = (5, 6)
    expected_move_rolls5 = [
        MoveRoll([Move(from_point=18, to_point=-1, move_type=MoveType.BEAR_OFF),
                  Move(from_point=18, to_point=23, move_type=MoveType.NORMAL), ]),
    ]

    return [('moves_start_position_1_2_white', game1, die_roll1, expected_move_rolls1),
            ('moves_start_position_6_7_black', game2, die_roll2, expected_move_rolls2),
            ('no_possible_moves_white', game3, die_roll3, expected_move_rolls3),
            ('bear_off_white_2_3', game4, die_roll4, expected_move_rolls4),
            ('bear_off_black_whit_normal_moves_5_6', game5, die_roll5, expected_move_rolls5)]


def apply_and_clone_game(game: BackgammonGame, mv_roll: MoveRoll) -> BackgammonGame:
    new_game = game.clone()
    new_game.apply_move_roll(mv_roll)
    return new_game


def are_move_move_roll_lists_equal(game: BackgammonGame, actual_move_rolls: List[MoveRoll],
                                   expected_move_rolls: List[MoveRoll]) -> bool:
    """
    Compares two lists of move rolls by gathering all end states of applying the moves in the move rolls
    and checking the differences
    """

    actual_states = sorted(
        set(map(lambda mv: apply_and_clone_game(game, mv).board.serialize_board(), actual_move_rolls)))
    expected_states = sorted(
        set(map(lambda mv: apply_and_clone_game(game, mv).board.serialize_board(), expected_move_rolls)))

    return actual_states == expected_states


class TestBackgammonGame(unittest.TestCase):

    @parameterized.expand(make_compute_game_state_test_data())
    def test_compute_game_state(self, _: str, game: BackgammonGame, expected_game_state: GameState):
        self.assertEqual(game.game_state_for_current_turn, expected_game_state)

    @parameterized.expand(make_apply_normal_moves_test_data())
    def test_apply_normal_moves(self, _: str, game: BackgammonGame, move_roll: Optional[MoveRoll],
                                expected_game: BackgammonGame):
        game.apply_move_roll(move_roll)
        self.assertEqual(game, expected_game,
                         f"Expected points: {expected_game.board}, actual points: {game.board}")

    @parameterized.expand(make_apply_normal_moves_test_data())
    def test_undo_normal_moves(self, _: str, expected_game: BackgammonGame, move_roll: Optional[MoveRoll],
                               game: BackgammonGame):
        game.undo_move_roll(move_roll)
        self.assertEqual(game, expected_game,
                         f"Expected points: {expected_game.board}, actual points: {game.board}")

    @parameterized.expand(make_checker_on_bar_moves_test_data())
    def test_apply_checker_on_bar_moves(self, _: str, game: BackgammonGame, move_roll: Optional[MoveRoll],
                                        expected_game: BackgammonGame):
        game.apply_move_roll(move_roll)
        self.assertEqual(game, expected_game,
                         f"Expected points: {expected_game.board}, actual points: {game.board}")

    @parameterized.expand(make_checker_on_bar_moves_test_data())
    def test_undo_checker_on_bar_moves(self, _: str, expected_game: BackgammonGame, move_roll: Optional[MoveRoll],
                                       game: BackgammonGame):
        game.undo_move_roll(move_roll)
        self.assertEqual(game, expected_game,
                         f"Expected points: {expected_game.board}, actual points: {game.board}")

    @parameterized.expand(make_bear_off_moves_test_data())
    def test_apply_bear_off_moves(self, _: str, game: BackgammonGame, move_roll: Optional[MoveRoll],
                                  expected_game: BackgammonGame):
        game.apply_move_roll(move_roll)
        self.assertEqual(game, expected_game,
                         f"Expected points: {expected_game.board}, actual points: {game.board}")

    @parameterized.expand(make_bear_off_moves_test_data())
    def test_undo_bear_off_moves(self, _: str, expected_game: BackgammonGame, move_roll: Optional[MoveRoll],
                                 game: BackgammonGame):
        game.undo_move_roll(move_roll)
        self.assertEqual(game, expected_game,
                         f"Expected points: {expected_game.board}, actual points: {game.board}")

    @parameterized.expand(make_valid_moves_test_data())
    def test_valid_moves(self, _: str, game: BackgammonGame, die_roll: Tuple[int, int], expected_moves: List[MoveRoll]):
        move_list = list(game.get_possible_move_rolls(die_roll))
        self.assertTrue(are_move_move_roll_lists_equal(game, move_list, expected_moves),
                        f"Expected moves: {expected_moves}, actual moves: {move_list}")
