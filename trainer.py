# 训练类，接受神经网络和数据，进行训练

import numpy as np
from collections import deque
import random
import time

class Trainer(object):
    def __init__(self,pv_net,bucket_size = 3000,batch_size=512):
        self.pv_net = pv_net
        self.bucket = deque(maxlen=3000)
        self.counter = 0

    @staticmethod
    def get_equi_data(play_data):
        """augment the data set by rotation and flipping
        play_data: [(state, mcts_prob, winner_z), ..., ...]
        TODO 这里能不能优化一下
        """
        extend_data = []
        for state, mcts_porb, winner in play_data:
            for i in [1, 2, 3, 4]:
                # rotate counterclockwise
                equi_state = np.array([np.rot90(s, i) for s in state])
                equi_mcts_prob = np.rot90(np.flipud(
                    mcts_porb.reshape(15,15)), i)
                extend_data.append((equi_state,
                                    np.flipud(equi_mcts_prob).flatten(),
                                    winner))
                # flip horizontally
                equi_state = np.array([np.fliplr(s) for s in equi_state])
                equi_mcts_prob = np.fliplr(equi_mcts_prob)
                extend_data.append((equi_state,
                                    np.flipud(equi_mcts_prob).flatten(),
                                    winner))
        return extend_data

    def policy_update(self,game_data):
        """update the policy-value net"""
        #define params
        enter_time = time.time()
        lr_multiplier = 1.0  # adaptively adjust the learning rate based on KL
        learn_rate = 2e-3 
        kl_targ = 0.02

        state_batch = [data[0] for data in game_data]
        mcts_probs_batch = [data[1] for data in game_data]
        winner_batch = [data[2] for data in game_data]
        old_probs, old_v = self.pv_net.policy_value(state_batch)
        for i in range(5):#self.epochs = 5  # num of train_steps for each update
            loss, entropy = self.pv_net.train_step(
                    state_batch,
                    mcts_probs_batch,
                    winner_batch,
                    learn_rate * lr_multiplier) #learn_rate = 2e-3 
            new_probs, new_v = self.pv_net.policy_value(state_batch)
            kl = np.mean(np.sum(old_probs * (
                    np.log(old_probs + 1e-10) - np.log(new_probs + 1e-10)),
                    axis=1)
            )
            if kl > kl_targ * 4:  # early stopping if D_KL diverges badly
                break
        # adaptively adjust the learning rate
        if kl > kl_targ * 2 and lr_multiplier > 0.1:
            lr_multiplier /= 1.5
        elif kl < kl_targ / 2 and lr_multiplier < 10:
            lr_multiplier *= 1.5

        explained_var_old = (1 -
                                np.var(np.array(winner_batch) - old_v.flatten()) /
                                np.var(np.array(winner_batch)))
        explained_var_new = (1 -
                                np.var(np.array(winner_batch) - new_v.flatten()) /
                                np.var(np.array(winner_batch)))
        time_cost = time.time() - enter_time
        print(("kl:{:.5f},"
                "lr_multiplier:{:.3f},"
                "loss:{},"
                "entropy:{},"
                "explained_var_old:{:.3f},"
                "explained_var_new:{:.3f},"
                "time cost:{:2f}"
                ).format(kl,
                        lr_multiplier,
                        loss,
                        entropy,
                        explained_var_old,
                        explained_var_new,
                        time_cost
                ))
        return loss, entropy

    def feed(self,data):
        self.counter +=1
        game_data = Trainer.get_equi_data(data)
        self.bucket.extend(game_data)
        if len(self.bucket) > 512:
            train_data = random.sample(self.bucket, 512)
            self.policy_update(train_data)
            self.pv_net.save_model()
