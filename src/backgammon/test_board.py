import unittest
from backgammon.agent.random_agent import RandomAgent

from backgammon.board import Board, Player


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
