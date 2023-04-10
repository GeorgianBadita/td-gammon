import tensorflow as tf

from src.model.model_tf import Model

graph = tf.Graph()
sess = tf.compat.v1.Session(graph=graph)

with sess.as_default(), graph.as_default():
    model = Model(sess, 'model/models/', 'model/summaries/', 'model/checkpoints/', False)
    model.train()
