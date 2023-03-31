from backgammon.agent.random_agent import RandomAgent
from backgammon.backgammon_game import BackgammonGame
from src.backgammon.board import Player

agent = RandomAgent(Player.WHITE, "Random agent")
game = BackgammonGame.new_game(agent, agent)
