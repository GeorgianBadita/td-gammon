from __future__ import division

import time
from itertools import count

import numpy as np
import tensorflow as tf

import src.backgammon_geobadita.agent.random_agent as rag
import src.backgammon_geobadita.agent.td_agent as ag
from src.backgammon_geobadita.backgammon_game import BackgammonGame
from src.backgammon_geobadita.board import Player


# helper to initialize a weight and bias variable
def weight_bias(shape):
    W = tf.Variable(tf.random.truncated_normal(shape, stddev=0.1), name='weight')
    b = tf.Variable(tf.constant(0.1, shape=shape[-1:]), name='bias')
    return W, b


# helper to create a dense, fully-connected layer
def dense_layer(x, shape, activation, name):
    with tf.compat.v1.variable_scope(name):
        W, b = weight_bias(shape)
        return activation(tf.matmul(x, W) + b, name='activation')


class Model(object):
    def __init__(self, sess, model_path, summary_path, checkpoint_path, restore=False):
        self.model_path = model_path
        self.summary_path = summary_path
        self.checkpoint_path = checkpoint_path

        # setup our session
        self.sess = sess
        self.global_step = tf.Variable(0, trainable=False, name='global_step')

        # lambda decay
        lamda = tf.maximum(0.7, tf.compat.v1.train.exponential_decay(0.9, self.global_step,
                                                                     30000, 0.96, staircase=True), name='lambda')

        # learning rate decay
        alpha = tf.maximum(0.01, tf.compat.v1.train.exponential_decay(0.1, self.global_step,
                                                                      40000, 0.96, staircase=True), name='alpha')

        tf.compat.v1.summary.scalar('lambda', lamda)
        tf.compat.v1.summary.scalar('alpha', alpha)

        # describe network size
        layer_size_input = 198
        layer_size_hidden = 40
        layer_size_output = 1

        # placeholders for input and target output
        self.x = tf.compat.v1.placeholder('float', [1, layer_size_input], name='x')
        self.V_next = tf.compat.v1.placeholder('float', [1, layer_size_output], name='V_next')

        # build network arch. (just 2 layers with sigmoid activation)
        prev_y = dense_layer(self.x, [layer_size_input, layer_size_hidden], tf.sigmoid, name='layer1')
        self.V = dense_layer(prev_y, [layer_size_hidden, layer_size_output], tf.sigmoid, name='layer2')

        # watch the individual value predictions over time
        tf.compat.v1.summary.scalar('V_next', tf.reduce_sum(input_tensor=self.V_next))
        tf.compat.v1.summary.scalar('V', tf.reduce_sum(input_tensor=self.V))

        # delta = V_next - V
        delta_op = tf.reduce_sum(input_tensor=self.V_next - self.V, name='delta')

        # mean squared error of the difference between the next state and the current state
        loss_op = tf.reduce_mean(input_tensor=tf.square(self.V_next - self.V), name='loss')

        # check if the model_geobadita predicts the correct state
        accuracy_op = tf.reduce_sum(
            input_tensor=tf.cast(tf.equal(tf.round(self.V_next), tf.round(self.V)), dtype='float'),
            name='accuracy')

        # track the number of steps and average loss for the current game
        with tf.compat.v1.variable_scope('game'):
            game_step = tf.Variable(tf.constant(0.0), name='game_step', trainable=False)
            game_step_op = game_step.assign_add(1.0)

            loss_sum = tf.Variable(tf.constant(0.0), name='loss_sum', trainable=False)
            delta_sum = tf.Variable(tf.constant(0.0), name='delta_sum', trainable=False)
            accuracy_sum = tf.Variable(tf.constant(0.0), name='accuracy_sum', trainable=False)

            loss_avg_ema = tf.train.ExponentialMovingAverage(decay=0.999)
            delta_avg_ema = tf.train.ExponentialMovingAverage(decay=0.999)
            accuracy_avg_ema = tf.train.ExponentialMovingAverage(decay=0.999)

            loss_sum_op = loss_sum.assign_add(loss_op)
            delta_sum_op = delta_sum.assign_add(delta_op)
            accuracy_sum_op = accuracy_sum.assign_add(accuracy_op)

            loss_avg_op = loss_sum / tf.maximum(game_step, 1.0)
            delta_avg_op = delta_sum / tf.maximum(game_step, 1.0)
            accuracy_avg_op = accuracy_sum / tf.maximum(game_step, 1.0)

            loss_avg_ema_op = loss_avg_ema.apply([loss_avg_op])
            delta_avg_ema_op = delta_avg_ema.apply([delta_avg_op])
            accuracy_avg_ema_op = accuracy_avg_ema.apply([accuracy_avg_op])

            tf.compat.v1.summary.scalar('game/loss_avg', loss_avg_op)
            tf.compat.v1.summary.scalar('game/delta_avg', delta_avg_op)
            tf.compat.v1.summary.scalar('game/accuracy_avg', accuracy_avg_op)
            tf.compat.v1.summary.scalar('game/loss_avg_ema', loss_avg_ema.average(loss_avg_op))
            tf.compat.v1.summary.scalar('game/delta_avg_ema', delta_avg_ema.average(delta_avg_op))
            tf.compat.v1.summary.scalar('game/accuracy_avg_ema', accuracy_avg_ema.average(accuracy_avg_op))

            # reset per-game monitoring variables
            game_step_reset_op = game_step.assign(0.0)
            loss_sum_reset_op = loss_sum.assign(0.0)
            self.reset_op = tf.group(*[loss_sum_reset_op, game_step_reset_op])

        # increment global step: we keep this as a variable, so it's saved with checkpoints
        global_step_op = self.global_step.assign_add(1)

        # get gradients of output V wrt trainable variables (weights and biases)
        tvars = tf.compat.v1.trainable_variables()
        grads = tf.gradients(ys=self.V, xs=tvars)

        # watch the weight and gradient distributions
        for grad, var in zip(grads, tvars):
            tf.compat.v1.summary.histogram(var.name, var)
            tf.compat.v1.summary.histogram(var.name + '/gradients/grad', grad)

        # for each variable, define operations to update the var with delta,
        # taking into account the gradient as part of the eligibility trace
        apply_gradients = []
        with tf.compat.v1.variable_scope('apply_gradients'):
            for grad, var in zip(grads, tvars):
                with tf.compat.v1.variable_scope('trace'):
                    # e-> = lambda * e-> + <grad of output w.r.t weights>
                    trace = tf.Variable(tf.zeros(grad.get_shape()), trainable=False, name='trace')
                    trace_op = trace.assign((lamda * trace) + grad)
                    tf.compat.v1.summary.histogram(var.name + '/traces', trace)

                # grad with trace = alpha * delta * e
                grad_trace = alpha * delta_op * trace_op
                tf.compat.v1.summary.histogram(var.name + '/gradients/trace', grad_trace)

                grad_apply = var.assign_add(grad_trace)
                apply_gradients.append(grad_apply)

        # as part of training we want to update our step and other monitoring variables
        with tf.control_dependencies([
            global_step_op,
            game_step_op,
            loss_sum_op,
            delta_sum_op,
            accuracy_sum_op,
            loss_avg_ema_op,
            delta_avg_ema_op,
            accuracy_avg_ema_op
        ]):
            # define single operation to apply all gradient updates
            self.train_op = tf.group(*apply_gradients, name='train')

        # merge summaries for TensorBoard
        self.summaries_op = tf.compat.v1.summary.merge_all()

        # create a saver for periodic checkpoints
        self.saver = tf.compat.v1.train.Saver(max_to_keep=1)

        # run variable initializers
        self.sess.run(tf.compat.v1.initialize_all_variables())

        # after training a model_geobadita, we can restore checkpoints here
        if restore:
            self.restore()

    def restore(self):
        latest_checkpoint_path = tf.train.latest_checkpoint(self.checkpoint_path)
        if latest_checkpoint_path:
            print('Restoring checkpoint: {0}'.format(latest_checkpoint_path))
            self.saver.restore(self.sess, latest_checkpoint_path)

    def get_output(self, x):
        return self.sess.run(self.V, feed_dict={self.x: x})

    def test(self, episodes=100, draw=False):
        agents = {Player.WHITE: ag.TDAgent(Player.WHITE, 'White agent', self),
                  Player.BLACK: rag.RandomAgent(Player.BLACK, 'Black agent')}
        winners = {Player.WHITE: 0, Player.BLACK: 0}

        for episode in range(episodes):
            env = BackgammonGame.new_game()
            agent_type, first_roll, observation = env.reset()
            if draw:
                env.draw()
            agent: ag.Agent = agents[agent_type]

            for _ in count():
                if first_roll:
                    roll = first_roll
                    first_roll = None
                else:
                    roll = env.roll_die()

                actions = list(env.get_possible_move_rolls(roll))
                action = agent.get_move(actions, env)
                _, _, done, _ = env.step(action)

                if draw:
                    print(f"Roll: {roll}, chosen move: {action}, by: {agent.player}")
                    env.draw()

                agent_type = env.get_and_set_opponent_turn()
                agent = agents[agent_type]

                if done:
                    break

            winner = env.winner
            winners[winner] += 1

            winners_total = sum([winners[Player.WHITE], winners[Player.BLACK]])
            print("[Episode %d] %s (%s) vs %s (%s) %d:%d of %d games (%.2f%%)" % (episode,
                                                                                  agents[Player.WHITE].name,
                                                                                  agents[Player.WHITE].player,
                                                                                  agents[Player.BLACK].name,
                                                                                  agents[Player.BLACK].player,
                                                                                  winners[Player.WHITE],
                                                                                  winners[Player.BLACK], winners_total,
                                                                                  (winners[
                                                                                       Player.WHITE] / winners_total) * 100.0))

    def train(self):
        tf.io.write_graph(self.sess.graph_def, self.model_path, 'td_gammon.pb', as_text=False)
        summary_writer = tf.compat.v1.summary.FileWriter(
            '{0}{1}'.format(self.summary_path, int(time.time()), self.sess.graph_def))

        # the agent plays against itself, making the best move for each player
        agents = {Player.WHITE: ag.TDAgent(Player.WHITE, 'White agent', self),
                  Player.BLACK: ag.TDAgent(Player.BLACK, 'Black agent', self)}

        validation_interval = 10_000
        episodes = 200_000
        wins = {Player.WHITE: 0, Player.BLACK: 0}

        for episode in range(episodes):
            if episode != 0 and episode % validation_interval == 0:
                self.test(episodes=100)

            env = BackgammonGame.new_game()
            agent_type, first_roll, observation = env.reset()
            agent: ag.Agent = agents[agent_type]
            observation = env.get_features(agent.player)
            reward = 0

            t = time.time()
            for _ in count():
                if first_roll:
                    roll = first_roll
                    first_roll = None
                else:
                    roll = env.roll_die()

                actions = list(env.get_possible_move_rolls(roll))
                action = agent.get_move(actions, env)
                observation_next, reward, done, info = env.step(action)

                v_next = self.get_output(observation_next)
                self.sess.run(self.train_op, feed_dict={self.x: observation, self.V_next: v_next})

                observation = observation_next
                agent_type = env.get_and_set_opponent_turn()
                agent = agents[agent_type]

                if done:
                    if env.winner is not None:
                        wins[env.winner] += 1

                    tot = sum(wins.values())
                    tot = tot if tot > 0 else 1

                    print(
                        "Game={:<6d} | Winner={} | after {:<4} plays || Wins: {}={:<6}({:<5.1f}%) | "
                        "{}={:<6}({:<5.1f}%) | Duration={:<.3f} sec".format(
                            episode + 1, env.winner, env.counter,
                            agents[Player.WHITE].name, wins[Player.WHITE], (wins[Player.WHITE] / tot) * 100,
                            agents[Player.BLACK].name, wins[Player.BLACK], (wins[Player.BLACK] / tot) * 100,
                            time.time() - t))

                    break

            _, global_step, summaries, _ = self.sess.run([
                self.train_op,
                self.global_step,
                self.summaries_op,
                self.reset_op
            ], feed_dict={self.x: observation, self.V_next: np.array([[reward]], dtype='float')})
            summary_writer.add_summary(summaries, global_step=global_step)
            self.saver.save(self.sess, self.checkpoint_path + 'checkpoint', global_step=global_step)

        summary_writer.close()

        self.test(episodes=1000)
