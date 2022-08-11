from enum import Enum, auto
import ansi
from wordle_requests import wotd
from wordle_image_processing import image_to_guess_list
from collections import Counter

class CharScore(Enum):
    CORRECT:    int = auto()
    MISPLACED:  int = auto()
    INCORRECT:  int = auto()

    def __str__(self):
        return self.name

class WordleGame:
    def __init__(self, image: bytes) -> None:
        self.image: bytes = image
        self.guesses: list[str] = image_to_guess_list(bytes=self.image)
        self.numGuesses: int = len(self.guesses)
        self.scores: list[list[CharScore]] = self._scoreGame()
        self.solution: str = wotd()
        self.won: bool = all(s == CharScore.CORRECT for s in self.scores[-1])

    # Returns the character, colored based on it's score.
    def _colorByScore(self, char, score) -> str:
        colored_char = ansi.ansi(char)

        # Correct: Character in the WOTD is identical in this position.
        if score == CharScore.CORRECT:
            return colored_char.green()

        # Misplaced: Character is present in the WOTD, but not this position.
        if score == CharScore.MISPLACED:
            return colored_char.yellow()

        # Incorrect: Character is not present in the WOTD.
        if score == CharScore.INCORRECT:
            return colored_char.gray()

        # Invalid Character Score!
        print(f'Invalid score type <{score}>. Returning original character.')
        return char

    # Assigns each character a CharScore.
    def _scoreGame(self) -> 'list[list[CharScore]]':
        # Score each guess
        scored = []
        for guess in self.guesses:
            guess_scores = [CharScore.INCORRECT] * 5
            wotd_char_counts = Counter(self.solution)
            unscored = []

            # Mark all correct characters
            for i, (gchar, wchar) in enumerate(zip(guess, self.solution)):
                if gchar == wchar:
                    wotd_char_counts[wchar] -= 1
                    guess_scores[i] = CharScore.CORRECT
                else:
                    unscored.append(i)

            # Mark all misplaced characters
            for index in unscored:
                gchar = guess[index]
                wchar = self.solution[index]
                if gchar in self.solution:
                    if wotd_char_counts[gchar] > 0:
                        wotd_char_counts[gchar] -= 1
                        guess_scores[index] = CharScore.MISPLACED
            
            scored.append(guess_scores)
        return scored

    # Returns a list of colored guesses according to the Wordle scheme.
    def pretty(self) -> 'list[str]':
        # For each guess...
        pretty = []
        for guess, scores in zip(self.guesses, self.scores):
            # For each character in the guess...
            str_score = ''
            for char, score in zip(guess, scores):
                str_score += self._colorByScore(char, score)
            pretty.append(str_score)
        return pretty
