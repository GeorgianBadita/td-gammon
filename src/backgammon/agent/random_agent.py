import random
from typing import List
from typing import Optional

from src.backgammon.agent.agent import Agent
from src.backgammon.backgammon_game import MoveRoll, BackgammonGame
from src.backgammon.board import Player


class RandomAgent(Agent):
    """
    Class representing a random agent
    """

    def __init__(self, player: Player, name: str):
        super().__init__(player, name)

    def get_move(
            self, move_rolls: List[MoveRoll], _: Optional[BackgammonGame] = None
    ) -> Optional[MoveRoll]:
        if len(move_rolls) == 0:
            return None

        return random.choice(move_rolls)
