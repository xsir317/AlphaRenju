from renju import RenjuBoard
import numpy as np

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
            debug_stone = '◯'
            if self.board.get_current_player():
                player = self.player1
                debug_stone = '●'
            move, move_probs = player.get_action(self.board)
            # store the data
            states.append(self.board.current_state())
            mcts_probs.append(move_probs)
            #print(move_probs)
            # perform a move
            self.board.do_move_by_number(move)
            print ("player: ",debug_stone)
            self.board._debug_board()
            #if len(states) >= 5:
            end, winner = self.board.game_end()
            if end:
                winner = RenjuBoard.WHITE_WIN
                total_moves = len(states)

                if winner == RenjuBoard.DRAW:
                    winner_map = [ 0 for _i in range(total_moves)]
                    print("draw")
                elif winner == RenjuBoard.WHITE_WIN:
                    winner_map = [ _i%2 for _i in range(total_moves)]
                    print("WHITE_WIN")
                else:
                    winner_map = [ (_i+1)%2 for _i in range(total_moves)]
                    print("BLACK_WIN")
                return winner, zip(states, mcts_probs,winner_map)
