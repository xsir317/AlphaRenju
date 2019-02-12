from game import Game
import numpy as np
from policy_value_net import PolicyValueNet
from players import MCTSPlayer

#new policy network
#new Game
#set game player
init_model = 'renju'
policy_value_net = PolicyValueNet(model_file=init_model)

#new MCTS
player = MCTSPlayer(policy_value_net.policy_value_fn,5,400,is_selfplay = 1)
game = Game(player,player)


def get_equi_data( play_data):
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


def policy_update(game_data,policy_value_net):
    """update the policy-value net"""
    #define params
    lr_multiplier = 1.0  # adaptively adjust the learning rate based on KL
    learn_rate = 2e-3 
    kl_targ = 0.02

    state_batch = [data[0] for data in game_data]
    mcts_probs_batch = [data[1] for data in game_data]
    winner_batch = [data[2] for data in game_data]
    old_probs, old_v = policy_value_net.policy_value(state_batch)
    for i in range(5):#self.epochs = 5  # num of train_steps for each update
        loss, entropy = policy_value_net.train_step(
                state_batch,
                mcts_probs_batch,
                winner_batch,
                learn_rate * lr_multiplier) #learn_rate = 2e-3 
        new_probs, new_v = policy_value_net.policy_value(state_batch)
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
    print(("kl:{:.5f},"
            "lr_multiplier:{:.3f},"
            "loss:{},"
            "entropy:{},"
            "explained_var_old:{:.3f},"
            "explained_var_new:{:.3f}"
            ).format(kl,
                    lr_multiplier,
                    loss,
                    entropy,
                    explained_var_old,
                    explained_var_new))
    return loss, entropy



while True:
    #game.do_play
    winner, game_data = game.do_play()
    game_data = list(game_data)[:]
    #get game data
    game_data = get_equi_data(game_data)
    #train ,update policy and save
    policy_update(game_data,policy_value_net)
    policy_value_net.save_model(init_model)
