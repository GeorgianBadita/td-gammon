from itertools import count

import tensorflow as tf

import src.backgammon.agent.human_agent as hag
import src.backgammon.agent.td_agent as ag
from src.backgammon.backgammon_game import BackgammonGame
from src.backgammon.board import Player
from src.model.model_tf import Model

graph = tf.Graph()
sess = tf.compat.v1.Session(graph=graph)

with sess.as_default(), graph.as_default():
    model = Model(sess, 'model/models/', 'model/summaries/', 'model/checkpoints/', True)
    agents = {Player.WHITE: ag.TDAgent(Player.WHITE, 'TD', model), Player.BLACK: hag.HumanAgent(Player.BLACK, 'Human')}

    env = BackgammonGame.new_game()
    agent_type, first_roll, observation = env.reset()

    env.draw()
    agent: ag.Agent = agents[agent_type]

    for _ in count():
        if first_roll:
            roll = first_roll
            first_roll = None
        else:
            roll = env.roll_die()

        actions = list(env.get_possible_move_rolls(roll))
        action = agent.get_move(actions, env, roll)
        _, _, done, _ = env.step(action)

        print(f"Roll: {roll}, chosen move: {action}, by: {agent.player}")
        env.draw()

        agent_type = env.get_and_set_opponent_turn()
        agent = agents[agent_type]

        if done:
            break
