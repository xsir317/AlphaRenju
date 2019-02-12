import numpy as np

#TODO 棋盘最好是一行一个int32， 实在不行换成数字也好
class RenjuBoard(object):
    EMPTY_STONE = 0 
    BLACK_STONE = 1
    WHITE_STONE = 2
    WHITE_FIVE = 1
    BLACK_FIVE = 2
    BLACK_FORBIDDEN = 4

    WHITE_WIN = -1
    BLACK_WIN = 1
    DRAW = 0

    directions = {
        '|' : [[+1,0],[-1,0]],    #下，上
        '-' : [[0,+1],[0,-1]],    #前，后
        '\\' : [[+1,+1],[-1,-1]], #右下，左上
        '/' : [[+1,-1],[-1,+1]],  #左下，右上
    }

    @staticmethod
    def get_oppo(stone):
        return 3 - stone

    def __init__(self,init = ''):
        self.reset(init)

    def reset(self,init = ''):
        self.width = 15
        self.height = 15
        self.last_move = 0
        self.availables = [i for i in range(225)]

        self.board = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,]
        self.current = [1,1]
        i = 0
    
        while i < len(init):
            self.do_move(init[i:i+2])
            i += 2

    def _debug_board(self):
        return_str = "\n "
        for x in range(15):
            return_str += "{:x}".format(x+1).center(4)
        return_str += "\r\n"
        for i in range(1,16):
            return_str += "{:x}".format(i)
            for j in range(1,16):
                if self._([i,j]) == RenjuBoard.BLACK_STONE:
                    return_str += '●'.center(3)
                elif self._([i,j]) == RenjuBoard.WHITE_STONE:
                    return_str += '◯'.center(3)
                else:
                    return_str += '-'.center(4)
            return_str += '\r\n\r\n'
        print (return_str)

    @staticmethod
    def pos2coordinate(position):
        return [
            int(position[0],16),
            int(position[1],16),
        ]

    @staticmethod
    def pos2number(position):
        return (int(position[0],16) - 1) * 15 + int(position[1],16) - 1

    @staticmethod
    def coordinate2pos(coordinate):
        return "{:x}{:x}".format(coordinate[0],coordinate[1])

    @staticmethod
    def num2coordinate(num):
        return [
            (num // 15) + 1 ,
            (num % 15) + 1 ,
        ]

    def do_move(self,pos):
        num = RenjuBoard.pos2number(pos)
        self.do_move_by_number(num)

    def do_move_by_number(self,number):
        coor = RenjuBoard.num2coordinate(number)
        color = RenjuBoard.WHITE_STONE
        if self.get_current_player():
            color = RenjuBoard.BLACK_STONE
        self.setStone(color,coor)
        self.last_move = number
        self.availables.remove(number)


    def _move_to(self,to = [8,8]):
        if to[0] >= 1 and to[0] <= 15 and to[1] >= 1 and to[1] <= 15:
            self.current = to
        return self._()

    def setStone(self,stone = 0,coordinate = []):
        if len(coordinate) == 0:
            coordinate = self.current
        
        row = self.board[coordinate[0] -1]
        row &= ~(1 << (coordinate[1] -1))
        row &= ~(1 << (coordinate[1] -1 + 16))
        if stone == self.WHITE_STONE:
            row |= (1 << (coordinate[1] -1 + 16))
        elif stone == self.BLACK_STONE:
            row |= (1 << (coordinate[1] -1))
        self.board[coordinate[0] -1] = row

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
        if self.board[coordinate[0] - 1] & (1 << coordinate[1] - 1) :
            return self.BLACK_STONE
        if self.board[coordinate[0] - 1] & (1 << coordinate[1] - 1 + 16):
            return self.WHITE_STONE
        return self.EMPTY_STONE

    def count_stone(self,coordinate,shape):
        color = self._(coordinate)
        if color == RenjuBoard.BLACK_STONE or color == RenjuBoard.WHITE_STONE:
            count = 1
            for direction in RenjuBoard.directions[shape]:
                self._move_to(coordinate)
                while color == self.moveDirection(direction):
                    count = count + 1
            return count
        return 0

    def isFive(self,coordinate,color,shape = '',rule = 'renju'):
        if self._(coordinate) != RenjuBoard.EMPTY_STONE:
            return False
        self.setStone(color,coordinate)
        result = False
        if shape:
            count = self.count_stone(coordinate,shape)
            result = self.count_as_five(count,color,rule)
        else:
            for s in RenjuBoard.directions.keys():
                count = self.count_stone(coordinate,s)
                result = self.count_as_five(count,color,rule)
                if result:
                    break
        self.setStone(RenjuBoard.EMPTY_STONE,coordinate)
        return result

    def isFour(self,coordinate,color, shape = ''):
        if shape == '':
            for s in RenjuBoard.directions.keys():
                result,defense_point = self.isFour(coordinate,color, s)
                if result :
                    return result,defense_point
            return result,defense_point
        defense_point = None
        if self._(coordinate) != RenjuBoard.EMPTY_STONE:
            return False,defense_point
        result = 0
        self.setStone(color,coordinate)
        count_stone = 1
        for direction in RenjuBoard.directions[shape]:
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
        self.setStone(RenjuBoard.EMPTY_STONE,coordinate)
        return result,defense_point

    def isOpenFour(self,coordinate,shape = '|'):
        if self._(coordinate) != RenjuBoard.EMPTY_STONE:
            return False
        count_active = 0
        self.setStone(RenjuBoard.BLACK_STONE,coordinate)
        count_black = 1
        for direction in RenjuBoard.directions[shape]:
            self._move_to(coordinate)
            while RenjuBoard.BLACK_STONE == self.moveDirection(direction):
                count_black = count_black + 1
            if self.isFive(self.current,RenjuBoard.BLACK_STONE,shape):
                count_active = count_active + 1
            else:
                break
        #恢复空格
        self.setStone(RenjuBoard.EMPTY_STONE,coordinate)
        if count_black == 4 and count_active == 2:
            if self.isForbidden(coordinate):
                return False
            return True
        return False

    def isOpenThree(self,coordinate,shape = '|'):
        result = False
        self.setStone(RenjuBoard.BLACK_STONE,coordinate)
        for direction in RenjuBoard.directions[shape]:
            self._move_to(coordinate)
            while RenjuBoard.BLACK_STONE == self.moveDirection(direction):
                None
            if self._() == RenjuBoard.EMPTY_STONE:
                if self.isOpenFour(self.current,shape):
                    result = True
                    break#能活四的话另一边不用看了，不能活四再看另一头
            else:#如果落子的地方有一头不是空格，那看也不用看了。。。
                break
        self.setStone(RenjuBoard.EMPTY_STONE,coordinate)
        return result

    def isDoubleThree(self,coordinate):
        count = 0
        for s in RenjuBoard.directions.keys():
            if self.isOpenThree(coordinate,s):
                count = count + 1
                if count >= 2:
                    return True
        return False

    def isDoubleFour(self,coordinate):
        count = 0
        for s in RenjuBoard.directions.keys():
            count_four,defense = self.isFour(coordinate,RenjuBoard.BLACK_STONE,s)
            count += count_four
            if count >= 2:
                return True
        return False

    def isOverline(self,coordinate):
        self.setStone(RenjuBoard.BLACK_STONE,coordinate)
        result = False
        for s in RenjuBoard.directions.keys():
            if self.count_stone(coordinate,s) > 5:
                result = True
                break

        self.setStone(RenjuBoard.EMPTY_STONE,coordinate)
        return result

    def count_as_five(self,number,color,rule = 'renju'):
        if color == RenjuBoard.WHITE_STONE and rule == 'renju':
            return number >= 5
        return number == 5

    def isForbidden(self,coordinate):
        if self._(coordinate) != RenjuBoard.EMPTY_STONE:
            return False
        if self.isFive(coordinate,RenjuBoard.BLACK_STONE):
            return False
        return (self.isOverline(coordinate) or self.isDoubleFour(coordinate) or self.isDoubleThree(coordinate))

    
    def VCF(self):
        vcf_path = []
        return_str = ''
        expands = []
        win = False
        win_by_forbidden = False
        
        #谁在冲四，谁在防
        attacker = (RenjuBoard.BLACK_STONE if self.get_current_player() else RenjuBoard.WHITE_STONE)
        defender = RenjuBoard.get_oppo(attacker)
        #构建一个搜索树，然后强行爬树。 反正vcf树不会大的，强行爬完就是了
        def expand_vcf(board): #return win, expand_points
            collect = []
            oppo_win = [] #这里检查对方是否可能获胜，也就是是否有对方的冲四要挡
            for i in range(1,16):
                for j in range(1,16):
                    if board.isFive([i,j],attacker):
                        return [i,j],[]
                    elif board.isFive([i,j],defender):
                        oppo_win.append([i,j])
                    count_four,defense = board.isFour([i,j],attacker)
                    if count_four > 0 and (attacker == RenjuBoard.WHITE_STONE or not board.isForbidden([i,j])):
                        collect.append([ [i,j] , defense])
            #走到这里的话，自己肯定是没连5， 检查对方的冲四点吧。
            if len(oppo_win) > 1:
                return False,[] #如果对方反冲四，而且还不止一个点，凉了
            if len(oppo_win) == 1:#如果对方反冲四，看看能不能再反冲四吧
                for _c in collect:
                    if oppo_win[0] == _c[0]:
                        return False,[ _c.copy() ]
                return False,[] #几个冲四点都没匹配，并不能反冲四，则此局面的确没有可行方案
            return False,collect



        while True:
            win , availables = expand_vcf(self)
            if win :
                break
            #一个优化，如果len(vcf_path) == 0 而且 availables也是空的，那么就是第一个局面就发现全盘无冲四，直接返回失败。
            if len(vcf_path) == 0 and len(availables) == 0:
                return None , ''
            expands.append(availables)

            while True:
                if len(expands) == 0:
                    break
                not_expanded = expands.pop()
                if(len(not_expanded) > 0):
                    break
                elif len(vcf_path) > 0:
                    to_remove = vcf_path.pop()#回溯
                    self.setStone(RenjuBoard.EMPTY_STONE,to_remove[0])
                    self.setStone(RenjuBoard.EMPTY_STONE,to_remove[1])

            if len(expands) == 0 and len(not_expanded) == 0:
                break
            next_try = not_expanded.pop()
            vcf_path.append(next_try)
            expands.append(not_expanded)
            if defender == RenjuBoard.BLACK_STONE and self.isForbidden(next_try[1]):
            #如果防守出现了禁手，那也是获胜了。 设置win 然后break
                win = next_try[1]
                win_by_forbidden = True
                break
            #走冲四
            self.setStone(attacker,next_try[0])
            #走防守
            self.setStone(defender,next_try[1])
        #这里检测win，拼接返回，
        if win:
            #最后一手是win
            for move_pair in vcf_path:
                return_str += RenjuBoard.coordinate2pos(move_pair[0])
                return_str += RenjuBoard.coordinate2pos(move_pair[1])
                self.setStone(RenjuBoard.EMPTY_STONE,move_pair[0])
                self.setStone(RenjuBoard.EMPTY_STONE,move_pair[1])
            if not win_by_forbidden:
                return_str += RenjuBoard.coordinate2pos(win)
        win_move = None
        if return_str:
            win_move = RenjuBoard.pos2number(return_str[0:2])
        return win_move , return_str

    def GetResult(self,player):
        is_end, winner = self.game_end()
        if is_end:
            if winner == RenjuBoard.DRAW:
                return RenjuBoard.DRAW
            if (player == 1 and winner == RenjuBoard.BLACK_WIN) or (player == 0 and winner == RenjuBoard.WHITE_WIN):
                return 1
            else:
                return 0
        return 0
        
    #已经落子之后， 调用此方法，从last_move获取最后落子点，来判断盘面胜负。
    def game_end(self):
        coordinate = RenjuBoard.num2coordinate(self.last_move)
        color = RenjuBoard.BLACK_STONE
        if self.get_current_player():# 这时候棋子已经落子了。 所以是反过来的
            color = RenjuBoard.WHITE_STONE
        self.setStone(RenjuBoard.EMPTY_STONE,coordinate)
        is_end, winner = self.checkWin(coordinate,color)
        self.setStone(color,coordinate)
        return is_end, winner

    #检测棋盘上指定点如果放下指定颜色的棋子，是否获胜。
    def checkWin(self,coordinate,color):
        #coordinate = self.pos2coordinate(position)
        if color == RenjuBoard.WHITE_STONE:
            if self.isFive(coordinate,color):
                return True,RenjuBoard.WHITE_WIN
        else:
            if self.isFive(coordinate,color):
                return True,RenjuBoard.BLACK_WIN
            if self.isForbidden(coordinate):
                return True,RenjuBoard.WHITE_WIN
        
        counting = 0
        for row in self.board:
            row_white = row >> 16
            row_black = row & 131071
            row_stones = row_black | row_white
            row_empty = 131071 - row_stones
            while row_empty > 0:
                if row_empty % 2:
                    counting += 1
                    if counting > 1:
                        return False , -1
                row_empty = row_empty >> 1
            
        return True, RenjuBoard.DRAW

    def gomokuCheckWin(self,coordinate,color):
        #coordinate = self.pos2coordinate(position)
        if self.isFive(coordinate,color,'','gomoku'):
            if color == RenjuBoard.BLACK_STONE:
                return RenjuBoard.BLACK_WIN
            else:
                return RenjuBoard.BLACK_WIN
        return False

    def get_current_player(self):
        return len(self.availables) % 2

    def dump_black(self):
        dump_map = []
        for i in range(1,16):
            row = []
            for j in range(1,16):
                if self._([i,j]) == RenjuBoard.BLACK_STONE:
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
                if self._([i,j]) == RenjuBoard.WHITE_STONE:
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
                if self._([i,j]) == RenjuBoard.EMPTY_STONE:
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
                if self.isFive([i,j],RenjuBoard.BLACK_STONE) or self.isFive([i,j],RenjuBoard.WHITE_STONE):
                    row.append(1)
                else:
                    row.append(0)
            dump_map.append(row)
        return dump_map

    
    def current_state(self):
        square_state = np.zeros((3, self.width, self.height))
        for i in range(15):
            for j in range(15):
                ijstone = self._([i+1,j+1])
                if ijstone == RenjuBoard.BLACK_STONE:
                    square_state[0][i][j] = 1
                elif ijstone == RenjuBoard.WHITE_STONE:
                    square_state[1][i][j] = 1
        square_state[2][:, :] = self.get_current_player()
        return square_state

#testboard = RenjuBoard('8889878698789a76979979a696a7aaa4a89577847346')
#testboard = RenjuBoard('8889878698789a76979979a696a7aaa4a895')
#testboard = RenjuBoard('88668776789698a6897584954849c8c95c37bcd7')
#testboard._debug_board()
#print(testboard.VCF())