import ansi

def __pretty_score_guess(guess, wotd):

    pretty_score = [ "" for _ in guess ]

    # Map each character in the guess to the number of occurrences
    wotd_occrs = { char: wotd.count(char)   for char in wotd }

    # First, handle characters in the correct position
    remains = []
    for i in range(5):
        _gi = guess[i]
        _wi = wotd[i]

        # if the guess is correct
        if _gi == _wi:
            pretty_score[i] = ansi.ansi(_gi).green()
            wotd_occrs[_wi] -= 1
        # otherwise, add index to remains list
        else:
            remains.append(i)

    # Then, handle misplaced and incorrect characters
    for i in remains:
        _gi = guess[i]
        _wi = wotd[i]

        # if the guess is within the wotd AND at least one unmarked occurence exists 
        if _gi in wotd and wotd_occrs[_wi] > 0:
            pretty_score[i] = ansi.ansi(_gi).yellow()
        else:
            pretty_score[i] = ansi.ansi(_gi).gray()

        wotd_occrs[_wi] -= 1
        
    return "".join(pretty_score)

def pretty_score_game(guess_list, wotd):
    pretty_print = [ __pretty_score_guess(guess, wotd) for guess in guess_list ]
    return pretty_print