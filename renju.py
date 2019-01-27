import numpy as np

#TODO 得把棋盘的b w 和 字符 . 换掉，最好是一行一个int32， 实在不行换成数字也好
class RenjuBoardTool(object):
    EMPTY_STONE = '.' 
    BLACK_STONE = 'b'
    WHITE_STONE = 'w'
    WHITE_FIVE = 1
    BLACK_FIVE = 2
    BLACK_FORBIDDEN = 4

    directions = {
        '|' : [[+1,0],[-1,0]],    #下，上
        '-' : [[0,+1],[0,-1]],    #前，后
        '\\' : [[+1,+1],[-1,-1]], #右下，左上
        '/' : [[+1,-1],[-1,+1]],  #左下，右上
    }

    def __init__(self,init = ''):
        self.reset(init)

    def reset(self,init = ''):
        self.width = 15
        self.height = 15
        self.last_move = '11'
        self.availables = []
        for i in range(1,16):
            for j in range(1,16):
                self.availables.append(self.coordinate2pos([i,j]))

        self.board = [
            ['.','.','.','.','.','.','.','.','.','.','.','.','.','.','.',],
            ['.','.','.','.','.','.','.','.','.','.','.','.','.','.','.',],
            ['.','.','.','.','.','.','.','.','.','.','.','.','.','.','.',],
            ['.','.','.','.','.','.','.','.','.','.','.','.','.','.','.',],
            ['.','.','.','.','.','.','.','.','.','.','.','.','.','.','.',],
            ['.','.','.','.','.','.','.','.','.','.','.','.','.','.','.',],
            ['.','.','.','.','.','.','.','.','.','.','.','.','.','.','.',],
            ['.','.','.','.','.','.','.','.','.','.','.','.','.','.','.',],
            ['.','.','.','.','.','.','.','.','.','.','.','.','.','.','.',],
            ['.','.','.','.','.','.','.','.','.','.','.','.','.','.','.',],
            ['.','.','.','.','.','.','.','.','.','.','.','.','.','.','.',],
            ['.','.','.','.','.','.','.','.','.','.','.','.','.','.','.',],
            ['.','.','.','.','.','.','.','.','.','.','.','.','.','.','.',],
            ['.','.','.','.','.','.','.','.','.','.','.','.','.','.','.',],
            ['.','.','.','.','.','.','.','.','.','.','.','.','.','.','.',],
        ]
        self.current = [1,1]
        i = 0
    
        while i < len(init):
            self.do_move(init[i:i+2])
            i += 2

    def _debug_board(self):
        print ("\n")
        for row in self.board:
            print (''.join(row))

    def pos2coordinate(self,position):
        return [
            int(position[0],16),
            int(position[1],16),
        ]
    
    def coordinate2pos(self,coordinate):
        return "{:x}{:x}".format(coordinate[0],coordinate[1])

    def do_move(self,pos):
        coor = self.pos2coordinate(pos)
        color = self.WHITE_STONE
        if self.get_current_player():
            color = self.BLACK_STONE
        self.setStone(color,coor)
        self.last_move = pos
        self.availables.remove(pos)


    def _move_to(self,to = [8,8]):
        if to[0] >= 1 and to[0] <= 15 and to[1] >= 1 and to[1] <= 15:
            self.current = to
        return self._()

    def setStone(self,stone = '.',coordinate = []):
        if len(coordinate) == 0:
            coordinate = self.current
        self.board[coordinate[0] -1][coordinate[1] -1] = stone

    def moveDirection(self,direction):
        next = [
            self.current[0] + direction[0],
            self.current[1] + direction[1],
        ]
        if next[0] < 1 or next[0] > 15 or next[1] < 1 or next[1] > 15:
            return False
        self.current = next
        return self._()

    def _(self,coordinate = []):
        if len(coordinate) == 0:
            coordinate = self.current
        return self.board[coordinate[0] -1][coordinate[1] -1]

    def count_stone(self,coordinate,shape):
        color = self._(coordinate)
        if color == RenjuBoardTool.BLACK_STONE or color == RenjuBoardTool.WHITE_STONE:
            count = 1
            for direction in RenjuBoardTool.directions[shape]:
                self._move_to(coordinate)
                while color == self.moveDirection(direction):
                    count = count + 1
            return count
        return 0

    def isFive(self,coordinate,color,shape = '',rule = 'renju'):
        if self._(coordinate) != RenjuBoardTool.EMPTY_STONE:
            return False
        self.setStone(color,coordinate)
        result = False
        if shape:
            count = self.count_stone(coordinate,shape)
            result = self.count_as_five(count,color,rule)
        else:
            for s in RenjuBoardTool.directions.keys():
                count = self.count_stone(coordinate,s)
                result = self.count_as_five(count,color,rule)
                if result:
                    break
        self.setStone(RenjuBoardTool.EMPTY_STONE,coordinate)
        return result

    def isFour(self,coordinate,color, shape = ''):
        if shape == '':
            for s in RenjuBoardTool.directions.keys():
                result,defense_point = self.isFour(coordinate,color, s)
                if result :
                    return result,defense_point
            return result,defense_point
        defense_point = None
        if self._(coordinate) != RenjuBoardTool.EMPTY_STONE:
            return False,defense_point
        result = 0
        self.setStone(color,coordinate)
        count_stone = 1
        for direction in RenjuBoardTool.directions[shape]:
            self._move_to(coordinate)
            while color == self.moveDirection(direction):
                count_stone = count_stone + 1
            current_Stone_copy = self.current.copy()
            if self.isFive(self.current,color,shape):#隐藏bug，这里self.current 会乱跑的。因为isFive 会带着current跑
                result = result + 1
                defense_point = current_Stone_copy.copy()
        #如果两边都能连5，则可能有一个特殊情况
        if count_stone == 4 and result == 2:
            result = 1
        #恢复空格
        self.setStone(RenjuBoardTool.EMPTY_STONE,coordinate)
        return result,defense_point

    def isOpenFour(self,coordinate,shape = '|'):
        if self._(coordinate) != RenjuBoardTool.EMPTY_STONE:
            return False
        count_active = 0
        self.setStone(RenjuBoardTool.BLACK_STONE,coordinate)
        count_black = 1
        for direction in RenjuBoardTool.directions[shape]:
            self._move_to(coordinate)
            while RenjuBoardTool.BLACK_STONE == self.moveDirection(direction):
                count_black = count_black + 1
            if self.isFive(self.current,RenjuBoardTool.BLACK_STONE,shape):
                count_active = count_active + 1
            else:
                break
        #恢复空格
        self.setStone(RenjuBoardTool.EMPTY_STONE,coordinate)
        if count_black == 4 and count_active == 2:
            if self.isForbidden(coordinate):
                return False
            return True
        return False

    def isOpenThree(self,coordinate,shape = '|'):
        result = False
        self.setStone(RenjuBoardTool.BLACK_STONE,coordinate)
        for direction in RenjuBoardTool.directions[shape]:
            self._move_to(coordinate)
            while RenjuBoardTool.BLACK_STONE == self.moveDirection(direction):
                None
            if self._() == RenjuBoardTool.EMPTY_STONE:
                if self.isOpenFour(self.current,shape):
                    result = True
                    break#能活四的话另一边不用看了，不能活四再看另一头
            else:#如果落子的地方有一头不是空格，那看也不用看了。。。
                break
        self.setStone(RenjuBoardTool.EMPTY_STONE,coordinate)
        return result

    def isDoubleThree(self,coordinate):
        count = 0
        for s in RenjuBoardTool.directions.keys():
            if self.isOpenThree(coordinate,s):
                count = count + 1
                if count >= 2:
                    return True
        return False

    def isDoubleFour(self,coordinate):
        count = 0
        for s in RenjuBoardTool.directions.keys():
            count_four,defense = self.isFour(coordinate,RenjuBoardTool.BLACK_STONE,s)
            count += count_four
            if count >= 2:
                return True
        return False

    def isOverline(self,coordinate):
        self.setStone(RenjuBoardTool.BLACK_STONE,coordinate)
        result = False
        for s in RenjuBoardTool.directions.keys():
            if self.count_stone(coordinate,s) > 5:
                result = True
                break

        self.setStone(RenjuBoardTool.EMPTY_STONE,coordinate)
        return result

    def count_as_five(self,number,color,rule = 'renju'):
        if color == RenjuBoardTool.WHITE_STONE and rule == 'renju':
            return number >= 5
        return number == 5

    def isForbidden(self,coordinate):
        if self._(coordinate) != RenjuBoardTool.EMPTY_STONE:
            return False
        if self.isFive(coordinate,RenjuBoardTool.BLACK_STONE):
            return False
        return (self.isOverline(coordinate) or self.isDoubleFour(coordinate) or self.isDoubleThree(coordinate))

    def try_vcf(self):
        vcf_path = []
        return_str = ''
        #先保证算法是对的，一会儿再优化
        #测试数据 8889878698789a76979979a696a7aaa4a89577847346
        #构建一个搜索树，然后强行爬树。 反正vcf树不会大的，强行爬完就是了
        #类似mcts，但是不用select，反正都要完整爬。
        #首先，根节点为当前局面。
        #先手（进攻，试图vcf）方只能搜索 isFive 和 isFour 且不是isForbidden 的点来作为available
        #如果对方有触发isFive 的点，且此点不available 则此走法被否定。
        #如果所有走法被否定则直接回溯到parent.parent （上一手进攻）走法被否定。
        #进攻方连五为胜
        #防守方被抓禁的话会触发的。
        #后手（防守方）只有一个策略，就是找对方isFive 点 来防。防守方不用去检查自己是否能连5，但是要返回自己落入禁手而失败的情况。 
        #进攻方获胜则回溯拿到整个path进行返回。
        #回溯到根节点下所有available被否定，则返回false
        #咱们就不clone了，直接来吧
        def expand_vcf(board): #return win, expand_points
            board._debug_board()
            collect = []
            curr_stone = (RenjuBoardTool.BLACK_STONE if board.get_current_player() else RenjuBoardTool.WHITE_STONE)
            for i in range(1,16):
                for j in range(1,16):
                    if board.isFive([i,j],curr_stone):
                        return [i,j],[]
                    count_four,defense = board.isFour([i,j],curr_stone)
                    if count_four > 0 and (curr_stone == RenjuBoardTool.WHITE_STONE or not board.isForbidden([i,j])):
                        collect.append([ [i,j] , defense])
            return False,collect
        
        #谁在冲四，谁在防
        attacker = (RenjuBoardTool.BLACK_STONE if self.get_current_player() else RenjuBoardTool.WHITE_STONE)
        defender = (RenjuBoardTool.WHITE_STONE if self.get_current_player() else RenjuBoardTool.BLACK_STONE)
        expands = []
        
        win = False
        win_by_forbidden = False
        while True:
            win , availables = expand_vcf(self)
            if win :
                break
            expands.append(availables)

            while True:
                if len(expands) == 0:
                    break
                not_expanded = expands.pop()
                if(len(not_expanded) > 0):
                    break
                else:
                    to_remove = vcf_path.pop()#回溯
                    self.setStone(RenjuBoardTool.EMPTY_STONE,to_remove[0])
                    self.setStone(RenjuBoardTool.EMPTY_STONE,to_remove[1])

            if len(expands) == 0 and len(not_expanded) == 0:
                break
            next_try = not_expanded.pop()
            vcf_path.append(next_try)
            expands.append(not_expanded)
            print ("doatk:{:s} dodef:{:s}".format(self.coordinate2pos(next_try[0]),self.coordinate2pos(next_try[1])))
            #走冲四
            self.setStone(attacker,next_try[0])
            #走防守
            if self.isForbidden(next_try[1]):
                win = next_try[1]
                win_by_forbidden = True
                break
            self.setStone(defender,next_try[1])
            #如果防守出现了禁手，那也是获胜了。 设置win 然后break
        #这里检测win，拼接返回，
        if win:
            #最后一手是win
            for move_pair in vcf_path:
                return_str += self.coordinate2pos(move_pair[0])
                return_str += self.coordinate2pos(move_pair[1])
                self.setStone(RenjuBoardTool.EMPTY_STONE,move_pair[0])
                self.setStone(RenjuBoardTool.EMPTY_STONE,move_pair[1])
            if not win_by_forbidden:
                return_str += self.coordinate2pos(win)

        return return_str

    #已经落子之后， 调用此方法，从last_move获取最后落子点，来判断盘面胜负。
    def game_end(self):
        coordinate = self.last_move
        color = self.BLACK_STONE
        if self.get_current_player():# 这时候棋子已经落子了。 所以是反过来的
            color = self.WHITE_STONE
        self.setStone(self.EMPTY_STONE,coordinate)
        is_end, winner = self.checkWin(coordinate,color)
        self.setStone(color,coordinate)
        return is_end, winner

    #检测棋盘上指定点如果放下指定颜色的棋子，是否获胜。
    def checkWin(self,coordinate,color):
        #coordinate = self.pos2coordinate(position)
        if color == RenjuBoardTool.WHITE_STONE:
            if self.isFive(coordinate,color):
                return True,0
        else:
            if self.isFive(coordinate,color):
                return True,1
            if self.isForbidden(coordinate):
                return True,0
        
        counting = 0
        for row in self.board:
            counting += row.count(RenjuBoardTool.EMPTY_STONE)
            if counting > 1:
                return False , -1
        return True, -1

    def gomokuCheckWin(self,coordinate,color):
        #coordinate = self.pos2coordinate(position)
        if self.isFive(coordinate,color,'','gomoku'):
            if color == RenjuBoardTool.BLACK_STONE:
                return RenjuBoardTool.BLACK_FIVE
            else:
                return RenjuBoardTool.WHITE_FIVE
        return False

    def get_current_player(self):
        return len(self.availables) % 2

    def dump_black(self):
        dump_map = []
        for i in range(1,16):
            row = []
            for j in range(1,16):
                if self._([i,j]) == RenjuBoardTool.BLACK_STONE:
                    row.append(1)
                else:
                    row.append(0)
            dump_map.append(row)
        return dump_map

    def dump_white(self):
        dump_map = []
        for i in range(1,16):
            row = []
            for j in range(1,16):
                if self._([i,j]) == RenjuBoardTool.WHITE_STONE:
                    row.append(1)
                else:
                    row.append(0)
            dump_map.append(row)
        return dump_map

    def dump_empty(self):
        dump_map = []
        for i in range(1,16):
            row = []
            for j in range(1,16):
                if self._([i,j]) == RenjuBoardTool.EMPTY_STONE:
                    row.append(1)
                else:
                    row.append(0)
            dump_map.append(row)
        return dump_map

    def dump_forbiddens(self):
        dump_map = []
        for i in range(1,16):
            row = []
            for j in range(1,16):
                if self.isForbidden([i,j]):
                    row.append(1)
                else:
                    row.append(0)
            dump_map.append(row)
        return dump_map

    def dump_win_points(self):
        dump_map = []
        for i in range(1,16):
            row = []
            for j in range(1,16):
                if self.isFive([i,j],RenjuBoardTool.BLACK_STONE) or self.isFive([i,j],RenjuBoardTool.WHITE_STONE):
                    row.append(1)
                else:
                    row.append(0)
            dump_map.append(row)
        return dump_map

    
    def current_state(self):
        #square_state = np.zeros((6, self.width, self.height))
        square_state = np.zeros((4, self.width, self.height))
        square_state[0] = self.dump_black()
        square_state[1] = self.dump_white()
        square_state[2] = self.dump_empty()
        #square_state[3] = self.dump_forbiddens()
        #square_state[4] = self.dump_win_points()
        square_state[3][:, :] = self.get_current_player()
        #return square_state[:, ::-1, :]
        return square_state

testboard = RenjuBoardTool('8889878698789a76979979a696a7aaa4a89577847346')
#testboard = RenjuBoardTool('8889878698789a76979979a696a78aaaa9a87577685765')
print(testboard.try_vcf())