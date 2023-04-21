from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, List, Tuple

import src.backgammon_geobadita.backgammon_game as bg


class Agent(ABC):
    """
    Abstract class for representing an agent
    """

    def __init__(self, player: bg.Player, name: str):
        self._player = player
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @property
    def player(self) -> bg.Player:
        return self._player

    @abstractmethod
    def get_move(
            self,
            move_rolls: List[bg.MoveRoll],
            backgammon_game: Optional[bg.BackgammonGame] = None,
            roll: Optional[Tuple[int, int]] = None
    ) -> Optional[bg.MoveRoll]:
        raise NotImplementedError(
            f"Method get_move must be implemented for {self.__class__}"
        )

    def __eq__(self, ot: "Agent") -> bool:
        return self.name == ot.name and self.__class__.__name__ == ot.__class__.__name__
