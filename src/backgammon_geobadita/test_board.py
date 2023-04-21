import unittest

from agent.random_agent import RandomAgent
from board import Player, Board


class TestBoard(unittest.TestCase):
    def test_initial_board_is_created_correct_white_agent_first(self):
        # ARRANGE
        white_agent = RandomAgent(Player.WHITE, "Random agent")
        # ACT
        game = Board.new_board(white_agent)
        # ASSERT
        self.assertEqual(game.points[0], -2)
        self.assertEqual(game.points[5], 5)
        self.assertEqual(game.points[7], 3)
        self.assertEqual(game.points[11], -5)
        self.assertEqual(game.points[12], 5)
        self.assertEqual(game.points[16], -3)
        self.assertEqual(game.points[18], -5)
        self.assertEqual(game.points[23], 2)
        self.assertEqual(game.turn, Player.WHITE)

    def test_initial_board_is_created_correct_black_agent_first(self):
        # ARRANGE
        black_agent = RandomAgent(Player.BLACK, "Random agent")
        # ACT
        game = Board.new_board(black_agent)
        # ASSERT
        self.assertEqual(game.points[0], -2)
        self.assertEqual(game.points[5], 5)
        self.assertEqual(game.points[7], 3)
        self.assertEqual(game.points[11], -5)
        self.assertEqual(game.points[12], 5)
        self.assertEqual(game.points[16], -3)
        self.assertEqual(game.points[18], -5)
        self.assertEqual(game.points[23], 2)
        self.assertEqual(game.turn, Player.BLACK)

    def test_serialize_deserialize_board(self):
        # ARRANGE
        white_agent = RandomAgent(Player.WHITE, "Random agent")
        game = Board.new_board(white_agent)
        # ACT
        serialized_game = game.serialize_board()
        # ASSERT
        self.assertEqual(
            serialized_game, Board.STARTING_BOARD_SERIALIZED_STARTING_WHITE
        )
        self.assertEqual(Board.from_string(serialized_game), game)

    def test_all_checkers_in_home_start_game(self):
        # ARRANGE
        white_agent = RandomAgent(Player.WHITE, "Random agent")
        game = Board.new_board(white_agent)
        # ACT
        all_checkers_in_home = game.all_checkers_in_home(Player.WHITE)
        # ASSERT
        self.assertFalse(all_checkers_in_home)

    def test_all_checkers_in_home_all_in_home_random_position(self):
        # ARRANGE
        white_agent = RandomAgent(Player.WHITE, "Random agent")
        game = Board.new_board(white_agent)
        game.points = [0] * 24
        game.points[0] = 2
        game.points[1] = 7
        game.points[5] = 5
        game.points[23] = 14
        game.inc_barred(Player.BLACK)
        game.inc_offed(Player.WHITE)
        # ACT
        all_checkers_in_home_w = game.all_checkers_in_home(Player.WHITE)
        all_checkers_in_home_b = game.all_checkers_in_home(Player.BLACK)
        # ASSERT
        self.assertTrue(all_checkers_in_home_w)
        self.assertFalse(all_checkers_in_home_b)

    def test_point_of_color(self):
        # ARRANGE
        white_agent = RandomAgent(Player.WHITE, "Random agent")
        game = Board.new_board(white_agent)
        # ACT
        is_0point_black = game.is_point_of_color(0, Player.BLACK)
        is_0point_white = game.is_point_of_color(0, Player.WHITE)
        is_12point_black = game.is_point_of_color(12, Player.BLACK)
        is_12point_white = game.is_point_of_color(12, Player.WHITE)
        is_empty_point_white = game.is_point_of_color(1, Player.WHITE)
        is_empty_point_black = game.is_point_of_color(1, Player.BLACK)
        # ASSERT
        self.assertTrue(is_0point_black)
        self.assertFalse(is_0point_white)
        self.assertTrue(is_12point_white)
        self.assertFalse(is_12point_black)
        self.assertFalse(is_empty_point_white)
        self.assertFalse(is_empty_point_black)

    def test_get_player_from_str_repr(self):
        # ASSERT
        self.assertEqual(Player.get_player_from_str_repr("b"), Player.BLACK)
        self.assertEqual(Player.get_player_from_str_repr("w"), Player.WHITE)

    def test_get_player_from_str_repr_invalid(self):
        # ASSERT
        with self.assertRaises(ValueError):
            Player.get_player_from_str_repr("s")
