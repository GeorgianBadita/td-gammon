from typing import List, Tuple
from typing import Optional

from src.backgammon_geobadita.agent.agent import Agent
from src.backgammon_geobadita.backgammon_game import MoveRoll, BackgammonGame
from src.backgammon_geobadita.board import Player


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

        mv_rolls_hist = [move_rolls]
        while True:
            try:
                show_string = "Proceed further: \n\t[s x,y] filters and keeps only move_rolls that have a move from x to y" \
                              "\n\t[u] undoes the last filtering" \
                              "\n\t[e idx] executes the idx-th move from the list\n\n"
                cmd = input(show_string).split(" ")
                if cmd[0] == 's':
                    flt = []
                    x, y = cmd[1].split(",")
                    for mv_roll in move_rolls:
                        tr = False
                        for mv in mv_roll.moves:
                            if mv.from_point == int(x) and mv.to_point == int(y):
                                tr = True
                                break
                        if tr:
                            flt.append(mv_roll)
                    mv_rolls_hist.append(flt)
                    move_rolls = flt
                    print("Possible moves: ")
                    for i, mv in enumerate(move_rolls):
                        print(f"Idx: {i}, mv: {mv}")
                elif cmd[0] == 'u':
                    if len(mv_rolls_hist) > 1:
                        move_rolls = mv_rolls_hist.pop()
                elif cmd[0] == 'e':
                    idx = int(cmd[1])
                    break
            except Exception as e:
                print(e)
                print("Invalid command. Try again")
        return move_rolls[idx]
