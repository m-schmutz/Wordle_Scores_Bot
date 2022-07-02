from enum import Enum, auto
import ansi

# CONSTANTS ################################################################################
############################################################################################
_DEBUG_PRINT: bool = False

class CharScore(Enum):
    CORRECT:    int = auto()
    MISPLACED:  int = auto()
    INCORRECT:  int = auto()



# USER FUNCTIONS ###########################################################################
############################################################################################

# pretty: __________________________________________________________________________________
# Returns a list of colored guesses according to the Wordle scheme:
#   - Correct: green
#   - Misplaced: yellow
#   - Incorrect: gray
def pretty(guess_list, game_scores):

    # Create a colored string for each guess
    pretty = []
    for guess, guess_scores in zip(guess_list, game_scores):

        # Generate the string by reading the score of each character of the current guess
        str_score = ""
        for char, score in zip(guess, guess_scores):
            
            char = ansi.ansi(char)
            if score == CharScore.CORRECT:      # Correct
                str_score += char.green()
            elif score == CharScore.MISPLACED:  # Misplaced
                str_score += char.yellow()
            elif score == CharScore.INCORRECT:  # Incorrect
                str_score += char.gray()
            else:                               # Unrecognized, boundary test
                quit("Unrecognized score type.")
        
        pretty.append(str_score)

    return pretty

# plain: ___________________________________________________________________________________
# Returns a list of raw guess scores.
def plain(guess_list, game_scores):

    plain = []
    for guess, guess_scores in zip(guess_list, game_scores):

        # Generate the string by reading the score of each character of the current guess
        str_score = []
        for char, score in zip(guess, guess_scores):
            
            char = ansi.ansi(char)
            if score == CharScore.CORRECT:      # Correct
                str_score.append(f"{char}: CORRECT")
            elif score == CharScore.MISPLACED:  # Misplaced
                str_score.append(f"{char}: MISPLACED")
            elif score == CharScore.INCORRECT:  # Incorrect
                str_score.append(f"{char}: INCORRECT")
            else:                               # Unrecognized, boundary test
                quit("Unrecognized score type.")
        
        plain.append(str_score)

    return plain

# score_game: ______________________________________________________________________________
# Assigns a score value (enum CharScore) to each letter in each guess
# and returns a list of the scores for each guess
def score_game(guess_list, wotd):

    init_gchar_scores = [ CharScore.INCORRECT ] * 5
    init_wchar_counts = { wchar: wotd.count(wchar) for wchar in wotd }

    # Simple helper function to copy the starting score of a guess
    # and the WOTD character counts
    def __init_chars():
        return init_gchar_scores.copy(), init_wchar_counts.copy()

    # Score each guess
    scored = []
    for guess in guess_list:
        gchar_scores, wchar_counts = __init_chars()

        # Mark all correct characters
        unscored = []
        for i, (gchar, wchar) in enumerate(zip(guess, wotd)):
            if gchar == wchar:
                wchar_counts[wchar] -= 1
                gchar_scores[i] = CharScore.CORRECT
            else:
                unscored.append(i)

        # Mark all misplaced characters
        for i in unscored:
            gchar = guess[i]
            wchar = wotd[i]

            if gchar in wotd:
                if wchar_counts[gchar] > 0:
                    wchar_counts[gchar] -= 1
                    gchar_scores[i] = CharScore.MISPLACED
        
        if _DEBUG_PRINT: print(f"\"{guess}\" raw score = {gchar_scores}")
        scored.append(gchar_scores)

    return scored
