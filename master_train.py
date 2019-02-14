from game import Game
#from policy_value_net import PolicyValueNet
from policy_value_net_residual import PolicyValueNet
from players import MasterPlayer
from trainer import Trainer

#new policy network
#new Game
#set game player
init_model = './master'
policy_value_net = PolicyValueNet(model_file=init_model)

trainer = Trainer(policy_value_net)
master = MasterPlayer()

while True:
    game_data = master.get_train_game()
    trainer.feed(game_data)
