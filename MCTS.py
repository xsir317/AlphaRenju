
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