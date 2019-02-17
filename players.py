import numpy as np
from mcts_alphaZero import MCTS
from renju import RenjuBoard

class Human(object):
    def __init__(self):
        None
    
    def get_action(self, board):
        location = input("Your move: (11 to ff)")
        #增加投降功能：
        if location == 'RESIGN':
            return None,None
        move_number = RenjuBoard.pos2number(location.strip())
        if move_number not in board.availables:
            print("invalid move")
            location = self.get_action(board)
        prob = np.zeros(15*15)
        prob[move_number] = 1.0
        return move_number,prob

    def notice(self,board,move):
        pass

    def __str__(self):
        return "Human"


class MCTSPlayer(object):
    """AI player based on MCTS"""

    def __init__(self, policy_value_function,
                 c_puct=5, n_playout=2000, is_selfplay=0,debug=False):
        self.mcts = MCTS(policy_value_function, c_puct, n_playout,debug = debug)
        self._is_selfplay = is_selfplay

    def reset_player(self):
        self.mcts.reset()

    def notice(self,board,move):
        #如果这里mcts的根是秃的，而且又必须要move，就直接重置之后expand 然后move
        #如果有问题可能得先reset啊
        self.mcts.update_with_move(board,move)

    def get_action(self, board, temp=1e-3):
        #sensible_moves = board.availables
        # the pi vector returned by MCTS as in the alphaGo Zero paper
        if self._is_selfplay:
            temp = 1.5
        move_probs = np.zeros(15*15)
        acts, probs = self.mcts.get_move_probs(board, temp)
        if acts is None: #ai认输
            return None,None
        move_probs[list(acts)] = probs
        best_chance = np.max(move_probs)
        best_move = np.where(move_probs == best_chance)[0][0]
        if self._is_selfplay:
            move = np.random.choice(
                acts,
                p = probs
                #p=0.9*probs + 0.1*np.random.dirichlet(0.3*np.ones(len(probs)))
            )
            #debug
            print ("choose ",RenjuBoard.number2pos(move) ,"by prob ",move_probs[move])
            print ("best move is ", RenjuBoard.number2pos(best_move), best_chance)
            # update the root node and reuse the search tree
        else:
            # with the default temp=1e-3, it is almost equivalent
            # to choosing the move with the highest prob
            #move = np.random.choice(acts, p=probs)
            move = best_move
            # reset the root node
            #self.mcts.update_with_move(-1)
        self.mcts.update_with_move(board,move)
        return move, move_probs


class MasterPlayer(object):
    """Master reads human game records"""

    def __init__(self,game_source = './games.log',jump_line = 0):
        self.file_reader = open(game_source, 'r')
        self.board = RenjuBoard()

    def get_train_game(self):
        game_string = self.file_reader.readline()
        print (game_string)
        self.board.reset()
        game_string = game_string.strip()
        states, mcts_probs = [], []
        #获得game 的记录和结果， 做一堆和self play 差不多的数据返回回去
        game_result = game_string.split(",")
        winner = int(game_result[1])
        for i in range(0,len(game_result[0]),2):
            pos = game_result[0][i:i+2]
            move_probs = np.zeros(15*15)
            move_number = RenjuBoard.pos2number(pos)
            move_probs[move_number] = 1.0
            # store the data

            states.append(self.board.current_state())
            mcts_probs.append(move_probs)
            self.board.do_move(pos)
            #self.board._debug_board()
            #if len(states) >= 5:
        total_moves = len(states)
        if winner == -1:
            winner_map = [ 0 for _i in range(total_moves)]
            print("draw")
        elif winner == 0: #white win
            winner_map = [ (_i%2) * 2 - 1 for _i in range(total_moves)]
            print("WHITE_WIN")
        else:
            winner_map = [ ((_i+1)%2)*2 - 1  for _i in range(total_moves)]
            print("BLACK_WIN")
        return zip(states, mcts_probs,winner_map)



class PolicyPlayer(object):
    """AI player based on MCTS"""

    def __init__(self, policy_value_function):
        self.policy_fn = policy_value_function

    def get_action(self, board):
        move_probs = np.zeros(15*15)
        action_probs, leaf_value = self.policy_fn(board)
        for action, prob in action_probs:
            move_probs[action] = prob
        best_chance = np.max(move_probs)
        best_move = np.where(move_probs == best_chance)[0][0]
        return best_move, move_probs

    def notice(self,board,move):
        pass