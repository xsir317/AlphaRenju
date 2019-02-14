from game import Game
#from policy_value_net import PolicyValueNet
from policy_value_net_residual import PolicyValueNet
from players import MCTSPlayer
from trainer import Trainer

#new policy network
#new Game
#set game player
#init_model = './renju'
init_model = './master'
policy_value_net = PolicyValueNet(model_file=init_model)

#new MCTS
player = MCTSPlayer(policy_value_net.policy_value_fn,5,1200,is_selfplay = 1)
game = Game(player,player)

trainer = Trainer(policy_value_net)


while True:
    winner, game_data = game.do_play()
    player.reset_player()
    #trainer.feed(game_data)