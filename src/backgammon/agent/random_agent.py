from typing import List
import random
from typing import Optional
from backgammon.agent.agent import Agent
from backgammon.backgammon_game import BackgammonGame, MoveRoll, Player


class RandomAgent(Agent):
    """
    Class representing a random agent
    """

    def __init__(self, player: Player, name: str) -> "RandomAgent":
        super().__init__(player, name)

    def get_move(
        self, move_rolls: List[MoveRoll], _: Optional[BackgammonGame] = None
    ) -> Optional[MoveRoll]:
        if len(move_rolls) == 0:
            return None

        return random.choice(move_rolls)
