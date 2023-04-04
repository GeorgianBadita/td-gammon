import time

from backgammon.agent.random_agent import RandomAgent
from backgammon.backgammon_game import BackgammonGame
from src.backgammon.board import Player

start = time.time()
agent_w = RandomAgent(Player.WHITE, "Random white agent")
agent_b = RandomAgent(Player.BLACK, "Random black agent")
game = BackgammonGame.new_game(agent_w, agent_b)
distribution = {Player.WHITE: 0, Player.BLACK: 0}
for idx in range(10000):
    new_game = game.clone()
    new_game.play(debug=False)
    distribution[new_game.winner] += 1
    # print(f"\n\nGame {idx} finished. Winner: {new_game.winner}")

print("=========DISTRIBUTION==========")
print(distribution)
end = time.time()

print(f"Time elapsed: {(end - start)}")
