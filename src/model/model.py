from __future__ import annotations

import datetime
import random
import time
from itertools import count
from typing import Dict

import numpy as np
import torch
import torch.nn as nn

import src.backgammon.agent.random_agent as rag
import src.backgammon.agent.td_agent as ag
from src.backgammon.backgammon_game import BackgammonGame
from src.backgammon.board import Player

torch.set_default_tensor_type('torch.DoubleTensor')


class TDGammonModel(nn.Module):
    def __init__(self, hidden_layer: int, lr: float, ld: float, init_weights: bool, input_layer: int = 198,
                 output_layer: int = 1, seed: int = 123):
        super(TDGammonModel, self).__init__()
        self.lr = lr
        self.lamda = ld  # It's lambda I know, but it's a reserved keyword
        self.start_episode = 0

        self.eligibility_traces = None
        self.optimizer = None

        torch.manual_seed(seed)
        random.seed(seed)

        self.hidden = nn.Sequential(
            nn.Linear(input_layer, hidden_layer),
            nn.Sigmoid()
        )

        self.output = nn.Sequential(
            nn.Linear(hidden_layer, output_layer),
            nn.Sigmoid()
        )

        if init_weights:
            self.init_weights()

    def init_eligibility_traces(self):
        self.eligibility_traces = [torch.zeros(weights.shape, requires_grad=False) for weights in
                                   list(self.parameters())]

    def save_checkpoint(self, checkpoint_path: str, step: int, experiment: str):
        path = checkpoint_path + "/{}_{}_{}.tar".format(experiment,
                                                        datetime.datetime.now().strftime('%Y%m%d_%H%M_%S_%f'), step + 1)
        save_dict = {'step': step + 1, 'model_state_dict': self.state_dict(),
                     'eligibility': self.eligibility_traces if self.eligibility_traces else []}

        if self.optimizer is not None:
            save_dict['optimizer'] = self.optimizer
        torch.save(save_dict, path)

        print(f"\nCheckpoint saved: {path}")

    def load_model(self, checkpoint_path: str, optimizer=None, eligibility=None):
        checkpoint = torch.load(checkpoint_path)
        self.start_episode = checkpoint['step']
        self.load_state_dict(checkpoint['model_state_dict'])

        if eligibility is not None:
            self.eligibility_traces = checkpoint['eligibility']

        if optimizer is not None:
            self.optimizer.load_state_dict(checkpoint['optimizer'])

    def init_weights(self):
        for param in self.parameters():
            nn.init.zeros_(param)

    def forward(self, x: np.ndarray) -> np.ndarray:
        x = torch.from_numpy(np.array(x))
        x = self.hidden(x)
        return self.output(x)

    def train(self, n_episodes: int, save_path: str, name_experiment: str, eligibility: bool = False,
              save_step: int = 0):
        start_episode = self.start_episode
        n_episodes += start_episode
        wins = {Player.WHITE: 0, Player.BLACK: 0}
        network = self

        agents = {Player.WHITE: ag.TDAgent(Player.WHITE, 'White Agent', network),
                  Player.BLACK: ag.TDAgent(Player.BLACK, 'Black Agent', network), }

        durations = []
        steps = 0
        start_training = time.time()

        for episode in range(start_episode, n_episodes):
            if eligibility:
                self.init_eligibility_traces()
            game = BackgammonGame.new_game(agents[Player.WHITE], agents[Player.BLACK])
            agent: ag.Agent = random.choice(list(agents.values()))
            observation = game.get_features(agent.player)

            t = time.time()
            for it in count():
                roll = game.roll_die()

                p = self(observation)

                game.board.turn = agent.player
                actions = list(game.get_possible_move_rolls(roll))
                action = agents[agent.player].get_move(actions, game)
                game.apply_move_roll(action)

                observation_next = game.get_features(Player.WHITE if agent == Player.BLACK else Player.BLACK)
                p_next = self(observation_next)

                if game.is_game_over:
                    if game.winner is not None:
                        self.update_weights(p, 1.0 if game.winner == Player.WHITE else 0)
                        wins[agent.player] += 1
                    tot = sum(wins.values())
                    tot = tot if tot > 0 else 1

                    print(
                        "Game={:<6d} | Winner={} | after {:<4} plays || Wins: {}={:<6}({:<5.1f}%) | {}={:<6}({:<5.1f}%) | "
                        "Duration={:<.3f} sec".format(
                            episode + 1, game.winner, it,
                            agents[Player.WHITE].name, wins[Player.WHITE], (wins[Player.WHITE] / tot) * 100,
                            agents[Player.BLACK].name, wins[Player.BLACK], (wins[Player.BLACK] / tot) * 100,
                            time.time() - t))

                    steps += it
                    durations.append(time.time() - t)
                    break
                else:
                    self.update_weights(p, p_next)

                agent = agents[Player.BLACK if agent.player == Player.WHITE else Player.WHITE]
                observation = game.get_features(Player.WHITE if agent == Player.BLACK else Player.BLACK)

            if save_path and save_step > 0 and episode > 0 and (episode + 1) % save_step == 0:
                self.save_checkpoint(checkpoint_path=save_path, step=episode, experiment=name_experiment)
                agents_to_evaluate = {Player.WHITE: ag.TDAgent(Player.WHITE, 'White agent', network),
                                      Player.BLACK: rag.RandomAgent(Player.BLACK, 'Black agent'), }
                self.evaluate_agents(agents_to_evaluate, n_episodes=20)
                print()
        print("\nAverage duration per game: {} seconds".format(round(sum(durations) / n_episodes, 3)))
        print("Average game length: {} plays | Total Duration: {}".format(round(steps / n_episodes, 2),
                                                                          datetime.timedelta(seconds=int(
                                                                              time.time() - start_training))))

        if save_path:
            self.save_checkpoint(checkpoint_path=save_path, step=n_episodes - 1, experiment=name_experiment)

            with open('{}/comments.txt'.format(save_path), 'a') as file:
                file.write("Average duration per game: {} seconds".format(round(sum(durations) / n_episodes, 3)))
                file.write("\nAverage game length: {} plays | Total Duration: {}".format(round(steps / n_episodes, 2),
                                                                                         datetime.timedelta(seconds=int(
                                                                                             time.time() - start_training))))

    def update_weights(self, p: torch.Tensor, p_next: float):
        # reset gradients
        self.zero_grad()

        p.backward()

        with torch.no_grad():
            td_error = p_next - p

            for i, w in enumerate(list(self.parameters())):
                self.eligibility_traces[i] = self.lamda * self.eligibility_traces[i] + w.grad
                new_weights = w + self.lr * td_error * self.eligibility_traces[i]
                w.copy_(new_weights)

        return td_error

    def evaluate_agents(self, agents: Dict[Player, ag.Agent], n_episodes: int):
        wins = {Player.WHITE: 0, Player.BLACK: 0}

        for episode in range(n_episodes):
            game = BackgammonGame.new_game(agents[Player.WHITE], agents[Player.BLACK])
            agent: ag.Agent = random.choice(list(agents.values()))
            t = time.time()
            for it in count():

                roll = game.roll_die()

                game.board.turn = agent.player
                actions = list(game.get_possible_move_rolls(roll))
                action = agents[agent.player].get_move(actions, game)
                game.apply_move_roll(action)

                if game.is_game_over:
                    if game.winner is not None:
                        wins[agent.player] += 1
                    tot = wins[Player.WHITE] + wins[Player.BLACK]
                    tot = tot if tot > 0 else 1

                    print(
                        "EVAL => Game={:<6d} | Winner={} | after {:<4} plays || Wins: {}={:<6}({:<5.1f}%) | {}={:<6}("
                        "{:<5.1f}%) | Duration={:<.3f} sec".format(
                            episode + 1, game.winner, it,
                            agents[Player.WHITE].name, wins[Player.WHITE], (wins[Player.WHITE] / tot) * 100,
                            agents[Player.BLACK].name, wins[Player.BLACK], (wins[Player.BLACK] / tot) * 100,
                            time.time() - t))
                    break

                agent = agents[Player.BLACK if agent.player == Player.WHITE else Player.WHITE]

        return wins


lr = 1e-4
hidden = 40
lamda = 0.7
init_weights = True
path = './checkpoints'
check = 'test_20230406_0357_20_243751_10000.tar'
td = TDGammonModel(hidden, lr, lamda, init_weights)
# td.load_model(f'{path}/{check}', optimizer=None, eligibility=True)
#
# agents_to_evaluate = {Player.WHITE: ag.TDAgent(Player.WHITE, 'White agent', td),
#                       Player.BLACK: rag.RandomAgent(Player.BLACK, 'Black agent'), }
#
# td.evaluate_agents(agents_to_evaluate, 1000)
td.train(1000000, path, 'test', True, 20000)
