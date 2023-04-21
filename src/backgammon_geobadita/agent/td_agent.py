from typing import List, Tuple
from typing import Optional

from src.backgammon_geobadita.agent.agent import Agent
from src.backgammon_geobadita.backgammon_game import MoveRoll, BackgammonGame
from src.backgammon_geobadita.board import Player


class TDAgent(Agent):
    """
    Class representing a td agent
    """

    def __init__(self, player: Player, name: str, net):
        super().__init__(player, name)
        self.model = net

    def get_move(
            self, move_rolls: List[MoveRoll], backgammon_game: Optional[BackgammonGame] = None,
            _: Optional[Tuple[int, int]] = None
    ) -> Optional[MoveRoll]:
        if len(move_rolls) == 0:
            return None

        if backgammon_game is None:
            raise ValueError('Backgammon game should not be None for TD agent')

        v_best = 0
        a_best = None
        env_clone = backgammon_game.clone()

        for a in move_rolls:
            observation, _, _, _ = env_clone.step(a)
            v = self.model.get_output(observation)
            v = 1. - v if self.player == Player.BLACK else v
            if v > v_best:
                v_best = v
                a_best = a
            env_clone.undo_move_roll(a)
            env_clone.counter -= 1
        return a_best
