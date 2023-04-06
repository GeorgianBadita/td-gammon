from typing import List
from typing import Optional

import numpy as np
from torch import nn

from src.backgammon.agent.agent import Agent
from src.backgammon.backgammon_game import MoveRoll, BackgammonGame
from src.backgammon.board import Player


class TDAgent(Agent):
    """
    Class representing a td agent
    """

    def __init__(self, player: Player, name: str, net: nn.Module):
        super().__init__(player, name)
        self.model = net

    def get_move(
            self, move_rolls: List[MoveRoll], backgammon_game: Optional[BackgammonGame] = None,
    ) -> Optional[MoveRoll]:
        if len(move_rolls) == 0:
            return None

        if backgammon_game is None:
            raise ValueError('Backgammon game should not be None for TD agent')

        vals = [0.0] * len(move_rolls)
        for i, move_roll in enumerate(move_rolls):
            backgammon_game.apply_move_roll(move_roll)
            vals[i] = self.model(backgammon_game.get_features(self.player)).detach().numpy()
            backgammon_game.undo_move_roll(move_roll)
        best_idx = int(np.argmax(vals)) if self.player == Player.WHITE else int(np.argmin(vals))

        return move_rolls[best_idx]
