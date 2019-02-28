#输入一个特定局面， 顾问会给出它认为的好点
#from renju import RenjuBoard
from renjuv2 import RenjuBoard
from players import MCTSPlayer
#from policy_value_net import PolicyValueNet
from policy_value_net_residual import PolicyValueNet

pv_net = PolicyValueNet('./master')

consultant = MCTSPlayer(pv_net.policy_value_fn,c_puct=10,n_playout=10000,debug=True)
board = RenjuBoard()

while True:
    board_str = input("What do you want?(e for exit)\n").strip()
    if board_str == 'e' or board_str == '':
        break
    board.reset(board_str)
    board._debug_board()
    consultant.reset_player()
    move,move_prob = consultant.get_action(board)
    #如果认输，显示一下
    if move is None :
        print ("got conclusion, resign")
    board.do_move_by_number(move)
    board._debug_board()


