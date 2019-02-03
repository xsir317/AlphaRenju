
#这是一个mcts的实现。
#五子棋是很容易猝死的游戏，对必胜/必败的归纳很容易得出一整个分支的胜负，所以这里着重实现了基于必胜、必败的归纳剪枝
#另外连续冲四导致的分支其实根本就不分叉，所以我们可以尝试VCF策略。 也算是用领域知识去剪枝吧。
# expand 打开一个节点的时候要遍历其所有可能走法
# 对其中每一个走法，如果它是获胜走法，或者必败走法，则标记自身，并且向上传播。
# 向上传播时，触发其父节点的check。
#         如果当前局面（节点）的所有可能走法（action）都是必败的，则它是必胜的；
#         如果当前局面（节点）的任意一个走法（action）是必胜的，则它是必败的；
#             发现必败走法时，需要标记自身， 删除子节点中 除了必胜之外的其他所有走法。
# 进行check 之后可能导致父节点自身的标记和向上传播。
# 标记包括标记此节点是不需要expand 的，结论明确的完全展开节点； 维护好visit 数不要变；
# 如果归纳到根节点必胜，也就是无论怎么走都是必败。。。 就随便返回个啥吧，返回第一个合法的走法就行了。
# 如果发现任何一个根节点下第一层的走法获胜，就返回此走法。

from math import sqrt,log
import random
from renju import RenjuBoard

class Node:
    """ A node in the game tree. Note wins is always from the viewpoint of playerJustMoved.
        Crashes if state not specified.
    """
    def __init__(self, move = None, parent = None,availabels = []):
        self.move = move # the move that got us to this node - "None" for the root node
        self.parentNode = parent # "None" for the root node
        self.childNodes = []
        self.wins = 0
        self.visits = 0
        self.untriedMoves = availabels # future child nodes 这里就要用神经网络去估计每个点的初始胜率 参考https://zhuanlan.zhihu.com/p/20607684 
        self.player = 1 - (len(availabels) % 2) # the only part of the state that the Node needs later
        #when init, if it's not terminal,check every untriedMoves see if it's terminal
        
    def UCTSelectChild(self):
        s = sorted(self.childNodes, key = lambda c: c.wins/c.visits + sqrt(2*log(self.visits)/c.visits))[-1]
        return s
    
    def AddChild(self, m, s):
        """ Remove m from untriedMoves and add a new child node for this move.
            Return the added child node
        """
        self.untriedMoves.remove(m)
        availabels = s.availabels
        player = 1 - (len(availabels) % 2)
        color = RenjuBoard.BLACK_STONE
        if player:
            color = RenjuBoard.WHITE_STONE
        #TODO check VCF
        for next_move in availabels:
            _end,_result = state.checkWin(RenjuBoard.pos2coordinate(next_move),color)
            if(_end):
                if (color == RenjuBoard.BLACK_STONE and _result == RenjuBoard.BLACK_WIN) or (color == RenjuBoard.WHITE_STONE and _result == RenjuBoard.WHITE_WIN):
                    child_win = 1
                elif _result == RenjuBoard.DRAW:
                    child_win = 0
                else:
                    child_win = -1
                #if one of the child wins, set terminal status
                if child_win == 1:
                    return None
                if child_win == -1:
                    availabels.remove(next_move)
        n = Node(move = m, parent = self, availabels = availabels)
        self.childNodes.append(n)
        return n
    
    # 对其中每一个走法，如果它是获胜走法，或者必败走法，则标记自身，并且向上传播。
    # 向上传播时，触发其父节点的check。
    #         如果当前局面（节点）的所有可能走法（action）都是必败的，则它是必胜的；
    #         如果当前局面（节点）的任意一个走法（action）是必胜的，则它是必败的；
    #             发现必败走法时，需要标记自身， 删除子节点中 除了必胜之外的其他所有走法。
    # 进行check 之后可能导致父节点自身的标记和向上传播。
    # 标记包括标记此节点是不需要expand 的，结论明确的完全展开节点； 维护好visit 数不要变；
    def Update(self, result):
        """ Update this node - one additional visit and result additional wins. result must be from the viewpoint of playerJustmoved.
        """
        self.visits += 1
        self.wins += result
        #if not self.is_terminal,  check all the child and update self
        child_best = -1
        child_terminated = True
        for _child in self.childNodes:
            if not _child.is_terminal:
                child_terminated = False
                continue
            if _child.result > child_best:
                child_best = _child.result
            if child_best == 1:
                break
        child_terminated = child_terminated and (len(self.untriedMoves) > 0)
        

    def __repr__(self):
        return "[M:" + str(self.move) + " W/V:" + str(self.wins) + "/" + str(self.visits) + " U:" + str(self.untriedMoves) + "]"

    def TreeToString(self, indent):
        s = self.IndentString(indent) + str(self)
        for c in self.childNodes:
             s += c.TreeToString(indent+1)
        return s

    def IndentString(self,indent):
        s = "\n"
        for i in range (1,indent+1):
            s += "| "
        return s

    def ChildrenToString(self):
        s = ""
        for c in self.childNodes:
             s += str(c) + "\n"
        return s


def UCT(rootstate, itermax, verbose = False):
    """ Conduct a UCT search for itermax iterations starting from rootstate.
        Return the best move from the rootstate.
        Assumes 2 alternating players (player 1 starts), with game results in the range [0.0, 1.0]."""

    rootnode = Node(state = rootstate)

    for i in range(itermax): #每跑一遍，树会展开一点
        node = rootnode
        state = rootstate.Clone() #copy 一个棋盘给这次爬树用

        # Select
        while node.untriedMoves == [] and node.childNodes != []: # node is fully expanded and non-terminal
            node = node.UCTSelectChild() #每次爬树的第一步，对每一个完全展开而且有子节点的节点， 通过 UCTSelectChild 往下爬 ！！！这个选择方式决定了深度还是广度的倾向性！！！
            state.do_move(node.move)#爬

        # Expand 如果爬到了一个没有完全探测的子节点，则
        # TODO 一个优化： 设置一个阈值， 子节点访问计数增加但是不着急展开，等计数超过N（设为40 参考知乎专栏介绍的优化思路）再做展开。
        if node.untriedMoves != []: # if we can expand (i.e. state/node is non-terminal)
            m = random.choice(node.untriedMoves)  #随便选个没探测过的子节点，打开它然后爬过去。。。 TODO 这里使用policy试试； 
            #检查一下这个会导致胜负么。。。
            #color = (RenjuBoard.BLACK_STONE if state.get_current_player() else RenjuBoard.WHITE_STONE)

            state.do_move(m)
            node = node.AddChild(m,state) # add child and descend tree 
            #在这里对有终结状态的untriedMoves直接处理掉。

        # Rollout - this can often be made orders of magnitude quicker using a state.GetRandomMove() function
        while state.GetMoves() != []: # while state is non-terminal  TODO 这里使用policy试试； 
            state.do_move(random.choice(state.GetMoves())) 

        # Backpropagate
        while node != None: # backpropagate from the expanded node and work back to the root node
            node.Update(state.GetResult(node.player)) # state is terminal. Update node with result from POV of node.playerJustMoved
            node = node.parentNode
            #check the return of the Update, and if root is terminal , do the return, it's over.

    # Output some information about the tree - can be omitted
    if (verbose): 
        print (rootnode.TreeToString(0))
    else: 
        print (rootnode.ChildrenToString())

    return sorted(rootnode.childNodes, key = lambda c: c.visits)[-1].move # return the move that was most visited
    #TODO 返回每个点的最终胜率