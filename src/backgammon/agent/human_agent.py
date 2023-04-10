from typing import List, Tuple
from typing import Optional

from src.backgammon.agent.agent import Agent
from src.backgammon.backgammon_game import MoveRoll, BackgammonGame
from src.backgammon.board import Player


class HumanAgent(Agent):
    """
    Class representing a human agent
    """

    def __init__(self, player: Player, name: str):
        super().__init__(player, name)

    def get_move(
            self, move_rolls: List[MoveRoll], backgammon_game: Optional[BackgammonGame] = None,
            roll: Optional[Tuple[int, int]] = None
    ) -> Optional[MoveRoll]:
        if len(move_rolls) == 0:
            return None

        print("Roll: ", roll)
        print("Possible moves: ")
        for i, mv in enumerate(move_rolls):
            print(f"Idx: {i}, mv: {mv}")
        return move_rolls[int(input("Enter move index: "))]
