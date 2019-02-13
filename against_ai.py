from game import Game
from policy_value_net import PolicyValueNet
from players import MCTSPlayer,Human
from trainer import Trainer

init_model = './master'
policy_value_net = PolicyValueNet(model_file=init_model)

trainer = Trainer(policy_value_net)

#new MCTS
player_ai = MCTSPlayer(policy_value_net.policy_value_fn,5,2000,is_selfplay = 0)
player_me = Human()
game = Game(player_ai,player_me)

while True:
    winner, game_data = game.do_play()
    player_ai.reset_player()
    trainer.feed(game_data) #这里我们加一个学习功能，让AI在和人对弈的时候也能学习。
