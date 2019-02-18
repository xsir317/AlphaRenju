# -*- coding: utf-8 -*-
"""
Monte Carlo Tree Search in AlphaGo Zero style, which uses a policy-value
network to guide the tree search and evaluate the leaf nodes

@author: Junxiao Song
"""

import numpy as np
import copy
from renju import RenjuBoard


def softmax(x):
    probs = np.exp(x - np.max(x))
    probs /= np.sum(probs)
    return probs


class TreeNode(object):
    """A node in the MCTS tree.

    Each node keeps track of its own value Q, prior probability P, and
    its visit-count-adjusted prior score u.
    """

    def __init__(self, parent, prior_p):
        self._parent = parent
        self._children = {}  # a map from action to TreeNode
        self._remain_count = 0
        self._n_visits = 0
        self._Q = 0
        self._u = 0
        self._P = prior_p
        self._lose = False
        self._win = False

    def expand(self, action_priors):
        """Expand tree by creating new children.
        action_priors: a list of tuples of actions and their prior probability
            according to the policy function.
        """
        for action, prob in action_priors:
            if action not in self._children:
                self._children[action] = TreeNode(self, prob)
        self._remain_count = len(self._children)

    def select(self, c_puct):
        """Select action among children that gives maximum action value Q
        plus bonus u(P).
        Return: A tuple of (action, next_node)
        """
        return max(self._children.items(),
                   key=lambda act_node: act_node[1].get_value(c_puct))

    def update(self, leaf_value,child_win = False,child_lose = False):
        """Like a call to update(), but applied recursively for all ancestors.
        """
        # If it is not root, this node's parent should be updated first.
        
        self._n_visits += 1
        # Update Q, a running average of values for all visits.
        self._Q += 1.0*(leaf_value - self._Q) / self._n_visits
        #如果_child 全lose 则当前update为win。仅当child 更新为lose 的时候，触发父节点的win检查。
        if child_win:
            self.mark_lose()
        if child_lose:
            self._remain_count -= 1
            if self._remain_count == 0:
                self.mark_win()
        #如果任何一个子节点 win了，则当前节点update为lose
        if self._parent:
            self._parent.update(-leaf_value,self._win,self._lose)

    def get_value(self, c_puct):
        """Calculate and return the value for this node.
        It is a combination of leaf evaluations Q, and this node's prior
        adjusted for its visit count, u.
        c_puct: a number in (0, inf) controlling the relative impact of
            value Q, and prior probability P, on this node's score.
        """
        if self._lose :
            return -999
        if self._win :
            return 1
        
        self._u = (c_puct * self._P *
                   np.sqrt(self._parent._n_visits) / (1 + self._n_visits))
        return self._Q + self._u

    def is_leaf(self):
        """Check if leaf node (i.e. no nodes below this have been expanded)."""
        return self._children == {} or self._win or self._lose

    def is_root(self):
        return self._parent is None

    def mark_lose(self):
        self._lose = True
        
        for act, _sub_node in self._children.items():
            if _sub_node._win == False :
                #_sub_node._children = {}
                _sub_node._P = 0
                _sub_node._n_visits = 0
        self._n_visits = 0
        self._Q = 0
        self._u = 0
        self._P = 0
        self._win = False

    def mark_win(self):
        self._win = True
        
        #self._n_visits = 0
        self._Q = 0
        self._u = 0
        self._P = 1
        self._lose = False


class MCTS(object):
    """An implementation of Monte Carlo Tree Search."""

    def __init__(self, policy_value_fn, c_puct=5, n_playout=10000,debug=False):
        """
        policy_value_fn: a function that takes in a board state and outputs
            a list of (action, probability) tuples and also a score in [-1, 1]
            (i.e. the expected value of the end game score from the current
            player's perspective) for the current player.
        c_puct: a number in (0, inf) that controls how quickly exploration
            converges to the maximum-value policy. A higher value means
            relying on the prior more.
        """
        self._root = TreeNode(None, 1.0)
        self._policy = policy_value_fn
        self._c_puct = c_puct
        self._n_playout = n_playout
        self.debug_mode = debug

    def _debug(self):
        if self.debug_mode:
            for act, _sub_node in self._root._children.items():
                if _sub_node._n_visits > 0:
                    print(RenjuBoard.number2pos(act),"\tsel ",_sub_node.get_value(self._c_puct),"\tv ",_sub_node._n_visits,"\tQ ",_sub_node._Q,"\tp ",_sub_node._P)

    def _playout(self, state):
        """
        从根节点开始跑一个playout，找到暂时没有结论的叶子节点
        确认其胜负，不确定的就采纳神经网络的结论值；
        """
        node = self._root
        while True:
            if node.is_leaf():
                break
            # 爬树，如果爬树了，那么root至少不是秃的
            action, node = node.select(self._c_puct)
            state.do_move_by_number(action)

        player = 1 - state.get_current_player() #应当是刚刚落子的那一方。
        leaf_value = None

        if not (node._win or node._lose):
            end, winner = state.game_end()
            if end:
                if winner == RenjuBoard.DRAW:  # tie
                    leaf_value = 0.0
                else:
                    if (player == 1 and winner == RenjuBoard.BLACK_WIN) or (player == 0 and winner == RenjuBoard.WHITE_WIN):
                        node.mark_win()
                    else:
                        node.mark_lose()
            else:
                win_move,only_defense,defense_count = state.Find_win()
                if win_move is not None:
                    node.mark_lose()
                #elif 有2个以上冲四点或者活四 or  防点是禁手
                elif (defense_count > 1) or (only_defense and state.get_current_player() == 1 and state.isForbidden(RenjuBoard.num2coordinate(only_defense))):
                    node.mark_win()
                else:#走到这里是没结论
                    if only_defense is not None: #如果有冲四就按照冲四防一下，往下走一手
                        node.expand( MCTS._build_expand_prob(state.availables,only_defense) )
                        node._remain_count = 1 #这里就剩唯一防了。
                        for act, _sub_node in node._children.items():
                            if act != only_defense:
                                _sub_node.mark_lose()
                        node = node._children[only_defense] #这里可以保证这个only_defense的落子不会触发胜负
                        state.do_move_by_number(only_defense)

                    action_probs, leaf_value = self._policy(state)
                    node.expand(action_probs)
                #当前局面下，轮到对手下棋，如果对方有获胜策略，则当前方输了。 

        if node._win :
            leaf_value = 1.0
        elif node._lose :
            leaf_value = -1.0

        node.update(leaf_value)
        root_result = self._root._win or self._root._lose or self._root._remain_count == 1
        if root_result and len(self._root._children) == 0:
            #TODO 对于有结论而没有expand 的根节点进行特殊处理。 因为再不处理， 这么返回的话， playout提前结束，就崩了。
            #如果根是秃的，那刚刚 state.Find_win() 肯定是对根做的，直接拿来用！ state也没动
            try:
                win_move
            except NameError:
                win_move,only_defense,defense_count = state.Find_win()
            if win_move:
                self._root.expand( MCTS._build_expand_prob(state.availables,win_move) )
                self._root._children[win_move].mark_win()
            else : 
                self._root.expand( MCTS._build_expand_prob(state.availables,only_defense) )

        return root_result

    def get_move_probs(self, state, temp=1e-3):
        """Run all playouts sequentially and return the available actions and
        their corresponding probabilities.
        state: the current game state
        temp: temperature parameter in (0, 1] controls the level of exploration
        """
        conclusion = False
        for n in range(self._n_playout):
            if n % 100 == 0:
                self._debug()
            state_copy = copy.deepcopy(state)
            conclusion = self._playout(state_copy)
            if conclusion:
                print ("got conclusion on root")
                break

        #remain 剩一个的时候，playout 直接跳出了。遍历一下，选择那个剩下的。
        if conclusion:
            if self._root._win: #根已经明确获胜了，就认输
                return None,None
            else:
                act_visits = []
                for act, node in self._root._children.items():
                    if self._root._lose:
                        if node._win:
                            act_visits.append((act,100))
                        else:
                            act_visits.append((act,0))
                    elif self._root._remain_count == 1:
                        if node._lose:
                            act_visits.append((act,0))
                        else:
                            act_visits.append((act,node._n_visits + 1))
        else:
            # calc the move probabilities based on visit counts at the root node
            act_visits = [(act, node._n_visits)
                        for act, node in self._root._children.items()]
        acts, visits = zip(*act_visits)
        act_probs = softmax(1.0/temp * np.log(np.array(visits) + 1e-10))
        return acts, act_probs

    def update_with_move(self, board,last_move):
        """Step forward in the tree, keeping everything we already know
        about the subtree.
        """
        if len(self._root._children) == 0:
            self.reset()
            self._root.expand( MCTS._build_expand_prob(board.availables,None) )
        if last_move in self._root._children:
            self._root = self._root._children[last_move]
            self._root._parent = None

    def reset(self):
        self._root = TreeNode(None, 1.0)

    @staticmethod
    def _build_expand_prob(legal_positions,act):
        probs = np.zeros(len(legal_positions))
        try:
            probs[legal_positions.index(act)] = 1
        except ValueError:
            probs[:] = 1/len(legal_positions)
        return zip(legal_positions, probs)

    def __str__(self):
        return "MCTS"
