#from renju import RenjuBoard
from renjuv2 import RenjuBoard
import numpy as np
import time

#一个游戏，要有一个棋盘，2个玩家，胜负结果，和返回数据。

class Game(object):
    def __init__(self,player1,player2):
        self.player1 = player1
        self.player2 = player2
        self.board = RenjuBoard()

    #初始化之后，就可以开始游戏了。
    #外面去控制开始比赛
    def do_play(self):
        self.board.reset()
        states, mcts_probs = [], []
        while True:
            player = self.player2
            opponent = self.player1
            debug_stone = '◯'
            if self.board.get_current_player():
                player = self.player1
                opponent = self.player2
                debug_stone = '●'
            move_start = time.time()
            move, move_probs = player.get_action(self.board)
            move_cost = time.time() - move_start
            #TODO  注意，在游戏进行时，Game类负责将当前棋局传递给当前棋手。
            # 棋手思考并得出结论，返回给Game；
            # Game负责将棋子落在棋盘上，然后应该是发一个全局的通知。 （发布：订阅模型）
            # 目前并没有这样做，只是通知落子的对方而已。
            opponent.notice(self.board,move) #Game在落子之后，要通知对手。
            #加入认输逻辑
            if move is None:
                end = True
                winner = (RenjuBoard.WHITE_WIN if self.board.get_current_player() else RenjuBoard.BLACK_WIN) #认输了，对手赢了
                print ("player: ",debug_stone," resigns.")
            else:
                # store the data
                states.append(self.board.current_state())
                mcts_probs.append(move_probs)
                #print(move_probs)
                # perform a move
                self.board.do_move_by_number(move)
                print ("player: ",debug_stone,"time: ",move_cost)
                self.board._debug_board()
                #if len(states) >= 5:
                end, winner = self.board.game_end()
            if end:
                total_moves = len(states)

                if winner == RenjuBoard.DRAW:
                    winner_map = [ 0 for _i in range(total_moves)]
                    print("draw")
                elif winner == RenjuBoard.WHITE_WIN:
                    winner_map = [ (_i%2) * 2 - 1 for _i in range(total_moves)]
                    print("WHITE_WIN")
                else:
                    winner_map = [ ((_i+1)%2)*2 - 1  for _i in range(total_moves)]
                    print("BLACK_WIN")
                return winner, zip(states, mcts_probs,winner_map)
