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

    def update(self, leaf_value,child_result = None):
        """Update node values from leaf evaluation.
        leaf_value: the value of subtree evaluation from the current player's
            perspective.
        """
        # Count visit.
        self._n_visits += 1
        # Update Q, a running average of values for all visits.
        self._Q += 1.0*(leaf_value - self._Q) / self._n_visits
        #如果_child 全lose 则当前update为win。仅当child 更新为lose 的时候，触发父节点的win检查。
        if child_result == 'lose':
            self._remain_count -= 1
            if self._remain_count == 0:
                self.mark_win()
                return 'win'
        #如果任何一个子节点 win了，则当前节点update为lose
        elif child_result == 'win':
            self.mark_lose()
            return 'lose'
        return None

    def update_recursive(self, leaf_value,child_result = None):
        """Like a call to update(), but applied recursively for all ancestors.
        """
        # If it is not root, this node's parent should be updated first.
        result = self.update(leaf_value,child_result)
        if self._parent:
            self._parent.update_recursive(-leaf_value,result)

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

    def __init__(self, policy_value_fn, c_puct=5, n_playout=10000):
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

    def _playout(self, state):
        """Run a single playout from the root to the leaf, getting a value at
        the leaf and propagating it back through its parents.
        State is modified in-place, so a copy must be provided.
        """
        node = self._root
        while(1):
            if node.is_leaf():
                break
            # Greedily select next move.
            action, node = node.select(self._c_puct)
            state.do_move_by_number(action)

        # Evaluate the leaf using a network which outputs a list of
        # (action, probability) tuples p and also a score v in [-1, 1]
        # for the current player.
        # Check for end of game.
        player = 1 - state.get_current_player() #应当是刚刚落子的那一方。
        if node._win :
            leaf_value = 1.0
            child_result = 'lose'
        elif node._lose :
            leaf_value = -1.0
            child_result = 'win'
        else:
            child_result = None
            end, winner = state.game_end()
            if end:
                if winner == RenjuBoard.DRAW:  # tie
                    leaf_value = 0.0
                else:
                    if (player == 1 and winner == RenjuBoard.BLACK_WIN) or (player == 0 and winner == RenjuBoard.WHITE_WIN):
                        leaf_value = 1.0
                        child_result = 'lose'
                        node.mark_win()
                    else:
                        leaf_value = -1.0
                        child_result = 'win'
            else:
                action_probs, leaf_value = self._policy(state)
                node.expand(action_probs)
                #当前局面下，轮到对手下棋，如果对方有获胜策略，则当前方输了。 
                #TODO 先Find_win ，如果能找到获胜手段，则可以避免一次 _policy 
                win_move = state.Find_win()
                if win_move:
                    leaf_value = -1.0
                    #node.mark_lose() 这个在后面的update里做过了
                    node._children[win_move].mark_win()
                    child_result = 'win'

        node.update_recursive(leaf_value,child_result) #TODO 这个值的符号到底对不对
        root_result = self._root._win or self._root._lose or self._root._remain_count == 1
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
                print ("playout",n," root remain:" ,self._root._remain_count)
            state_copy = copy.deepcopy(state)
            conclusion = self._playout(state_copy)
            if conclusion:
                print ("got conclusion on root")
                break

        #TODO root 输了的时候的特殊处理，不处理的话会不会所有点visit都是0
        #remain 剩一个的时候，playout 直接跳出了。遍历一下，选择那个剩下的。
        if conclusion:
            act_visits = []
            for act, node in self._root._children.items():
                if self._root._win:
                    act_visits.append((act,node._n_visits + 1))
                elif self._root._lose:
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

    def update_with_move(self, last_move):
        """Step forward in the tree, keeping everything we already know
        about the subtree.
        """
        if last_move in self._root._children:
            self._root = self._root._children[last_move]
            self._root._parent = None
        else:
            self._root = TreeNode(None, 1.0)

    def __str__(self):
        return "MCTS"
