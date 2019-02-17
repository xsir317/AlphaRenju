from game import Game
#from policy_value_net import PolicyValueNet
from policy_value_net_residual import PolicyValueNet
from players import MCTSPlayer,PolicyPlayer

#new policy network
#new Game
#set game player
#init_model = './renju'
init_model = './master'
policy_value_net = PolicyValueNet(model_file=init_model)

#new MCTS
player = MCTSPlayer(policy_value_net.policy_value_fn,5,1000,is_selfplay = 1)
player_policy = PolicyPlayer(policy_value_net.policy_value_fn)
game = Game(player_policy,player)



while True:
    winner, game_data = game.do_play()
    player.reset_player()