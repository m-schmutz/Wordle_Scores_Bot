from datetime import datetime
from wordle import _gameAnalyzer

ga = _gameAnalyzer()
with open('./lib/images/test-games/wordle-game-light5.png', 'rb') as fd:
    image = fd.read()
ga.scoreGame(image, datetime.now().date())