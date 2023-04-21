import tensorflow as tf

from src.model_geobadita.model_tf import Model

graph = tf.Graph()
sess = tf.compat.v1.Session(graph=graph)

with sess.as_default(), graph.as_default():
    model = Model(sess, 'model_geobadita/models/', 'model_geobadita/summaries/', 'model_geobadita/checkpoints/', False)
    model.train()
