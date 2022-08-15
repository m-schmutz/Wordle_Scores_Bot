import random

# board = [ None ] * 25

# for i in range(6):
#     cell = random.randint(0, 24)
#     while board[cell]:
#         cell = random.randrange(0, 25)
    
#     board[cell] = i + 1

# print(board)

class ChimpView():
    def __init__(self):
        # super().__init__()
        self._boardSize = 25
        self._defaultBoard = [None] * self._boardSize
        self._defaultLevel = 6

        self.board = self._resetBoard()
        self.level = self._defaultLevel

        # for i in range(25):
        #     button = discord.ui.Button(
        #         style=discord.ButtonStyle.red,
        #         label=str(i))
        #     self.add_item(button)

    def _resetBoard(self):
        return self._defaultBoard.copy()
        
    def _randomizeBoard(self, num: int):
        self.board = self._resetBoard()
        for i in range(num):
            cell = random.randrange(0, self._boardSize)
            while self.board[cell]:
                cell = random.randrange(0, self._boardSize)
    
            self.board[cell] = i + 1

a = ChimpView()
print(a.board)
input('randomize? >')
a._randomizeBoard(6)
print(a.board)
input('reset? >')
a._resetBoard()
print(a.board)
input('randomize? >')
a._randomizeBoard(6)
print(a.board)
input('reset? >')
a._resetBoard()
print(a.board)