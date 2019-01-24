from renju import RenjuBoardTool

#一个游戏，要有一个棋盘，2个玩家，胜负结果，和返回数据。

class Game(object):
    def __init__(self,player1,player2):
        self.player1 = player1
        self.player2 = player2
        self.board = RenjuBoardTool()

    #初始化之后，就可以开始游戏了。
    #外面去控制开始比赛
    def do_play(self):
        result = 0 #比赛结果，黑方视角， 赢了是1分 输了是0  和棋0.5
        return_data = []

        self.board.reset()
        

        return result,return_data
        