from backgammon.agent.random_agent import RandomAgent
from backgammon.backgammon_game import BackgammonGame
from src.backgammon.board import Player

agent = RandomAgent(Player.WHITE, "Random agent")
game = BackgammonGame.new_game(agent, agent)
# game.play(debug=True)

two_one = game.get_possible_move_rolls((2, 1))
print(two_one)
print(len(two_one))
