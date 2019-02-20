# -*- coding: utf-8 -*-
import numpy as np
import tensorflow as tf


class PolicyValueNet():
    def __init__(self, model_file=None):
        self.model_file = model_file
        self.loss_weight = [1.0,0.1] # policy weight and value weight

        # 1. Input:
        self.input_states = tf.placeholder(
                tf.float32, shape=[None, 3, 15, 15])
        self.input_state = tf.transpose(self.input_states, [0, 2, 3, 1])
        # 2. Common Networks Layers
        self.conv1 = tf.layers.conv2d(inputs=self.input_state,
                                      filters=256, kernel_size=[3, 3],
                                      padding="same", data_format="channels_last",
                                      activation=None)
        self.conv1 = tf.layers.batch_normalization(self.conv1)
        self.conv1 = tf.nn.relu(self.conv1)
        
        for i in range(5):
            self.conv1 = self._build_residual_block(self.conv1, i)
        
        
        self.conv1 = tf.layers.conv2d(inputs=self.conv1,
                                      filters=256, kernel_size=[3, 3],
                                      padding="same", data_format="channels_last",
                                      activation=None)
        self.conv1 = tf.layers.batch_normalization(self.conv1)
        self.conv1 = tf.nn.relu(self.conv1)

        # 3-1 Action Networks
        self.action_conv = tf.layers.conv2d(inputs=self.conv1, filters=3,
                                            kernel_size=[1, 1], padding="same",
                                            data_format="channels_last",
                                            activation=tf.nn.relu)
        # Flatten the tensor
        self.action_conv_flat = tf.reshape(
                self.action_conv, [-1, 3 * 15 * 15])
        # 3-2 Full connected layer, the output is the log probability of moves
        # on each slot on the board
        self.action_fc = tf.layers.dense(inputs=self.action_conv_flat,
                                         units=15 * 15,
                                         activation=tf.nn.log_softmax)
        # 4 Evaluation Networks
        self.evaluation_conv = tf.layers.conv2d(inputs=self.conv1, filters=2,
                                                kernel_size=[1, 1],
                                                padding="same",
                                                data_format="channels_last",
                                                activation=tf.nn.relu)
        self.evaluation_conv_flat = tf.reshape(
                self.evaluation_conv, [-1, 2 * 15 * 15])
        self.evaluation_fc1 = tf.layers.dense(inputs=self.evaluation_conv_flat,
                                              units=64, activation=tf.nn.relu)
        # output the score of evaluation on current state
        self.evaluation_fc2 = tf.layers.dense(inputs=self.evaluation_fc1,
                                              units=1, activation=tf.nn.tanh)

        # Define the Loss function
        # 1. Label: the array containing if the game wins or not for each state
        self.labels = tf.placeholder(tf.float32, shape=[None, 1])
        # 2. Predictions: the array containing the evaluation score of each state
        # which is self.evaluation_fc2
        # 3-1. Value Loss function
        self.value_loss = tf.losses.mean_squared_error(self.labels,
                                                       self.evaluation_fc2)
        # 3-2. Policy Loss function
        self.mcts_probs = tf.placeholder(
                tf.float32, shape=[None, 15 * 15])
        self.policy_loss = tf.negative(tf.reduce_mean(
                tf.reduce_sum(tf.multiply(self.mcts_probs, self.action_fc), 1)))
        # 3-3. L2 penalty (regularization)
        l2_penalty_beta = 1e-4
        vars = tf.trainable_variables()
        l2_penalty = l2_penalty_beta * tf.add_n(
            [tf.nn.l2_loss(v) for v in vars if 'bias' not in v.name.lower()])
        # 3-4 Add up to be the Loss function
        self.loss = self.loss_weight[0] * self.policy_loss + self.loss_weight[1] * self.value_loss + l2_penalty

        # Define the optimizer we use for training
        self.learning_rate = tf.placeholder(tf.float32)
        self.optimizer = tf.train.AdamOptimizer(
                learning_rate=self.learning_rate).minimize(self.loss)

        # Make a session
        self.session = tf.Session()

        # calc policy entropy, for monitoring only
        self.entropy = tf.negative(tf.reduce_mean(
                tf.reduce_sum(tf.exp(self.action_fc) * self.action_fc, 1)))

        # Initialize variables
        init = tf.global_variables_initializer()
        self.session.run(init)

        # For saving and restoring
        self.saver = tf.train.Saver()
        if self.model_file is not None and tf.train.checkpoint_exists(self.model_file):
            self.restore_model()
            print ("restore from :" , self.model_file)
        else:
            print ("no file to load")


    def _build_residual_block(self, x, index):
        res_x = x
        res_name = "res" + str(index)
        x = tf.layers.conv2d(inputs=x,
                                    filters=256, kernel_size=[3, 3],use_bias=False,name=res_name+"_conv1",
                                    padding="same", data_format="channels_last",
                                    activation=None)
        x = tf.layers.batch_normalization(x,name=res_name+"_batchnorm1")
        x = tf.nn.relu(x,name=res_name+"_relu1")
        
        x = tf.layers.conv2d(inputs=x,
                                    filters=256, kernel_size=[3, 3],use_bias=False,name=res_name+"_conv2",
                                    padding="same", data_format="channels_last",
                                    activation=None)
        x = tf.layers.batch_normalization(x,name=res_name+"_batchnorm2")
        x = res_x + x
        x = tf.nn.relu(x,name=res_name+"_relu2")
        return x


    def policy_value(self, state_batch):
        """
        input: a batch of states
        output: a batch of action probabilities and state values
        """
        log_act_probs, value = self.session.run(
                [self.action_fc, self.evaluation_fc2],
                feed_dict={self.input_states: state_batch}
                )
        act_probs = np.exp(log_act_probs)
        return act_probs, value

    def policy_value_fn(self, board):
        """
        input: board
        output: a list of (action, probability) tuples for each available
        action and the score of the board state
        """
        legal_positions = board.availables
        current_state = np.ascontiguousarray(board.current_state().reshape(
                -1, 3, 15, 15))
        act_probs, value = self.policy_value(current_state)
        act_probs = zip(legal_positions, act_probs[0][legal_positions])
        return act_probs, value

    def train_step(self, state_batch, mcts_probs, winner_batch, lr):
        """perform a training step"""
        winner_batch = np.reshape(winner_batch, (-1, 1))
        loss, entropy, _ = self.session.run(
                [self.loss, self.entropy, self.optimizer],
                feed_dict={self.input_states: state_batch,
                           self.mcts_probs: mcts_probs,
                           self.labels: winner_batch,
                           self.learning_rate: lr})
        return loss, entropy

    def save_model(self):
        self.saver.save(self.session, self.model_file)

    def restore_model(self):
        self.saver.restore(self.session, self.model_file)
