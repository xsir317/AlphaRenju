#输入一个特定局面， 顾问会给出它认为的好点
from renju import RenjuBoard
from players import MCTSPlayer
from policy_value_net import PolicyValueNet

pv_net = PolicyValueNet('./master')

consultant = MCTSPlayer(pv_net.policy_value_fn,n_playout=10000)
board = RenjuBoard()

while True:
    board_str = input("What do you want?(e for exit)\n").strip()
    if board_str == 'e':
        break
    board.reset(board_str)
    board._debug_board()
    consultant.reset_player()
    move,move_prob = consultant.get_action(board)
    board.do_move_by_number(move)
    board._debug_board()


