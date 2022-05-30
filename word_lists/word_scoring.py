#!./env/bin/python3
########################################################################################
# scores for a green and yellow letters
# grey letters have score 0
GREEN_SCORE = 20
YELLOW_SCORE = 10
########################################################################################
# this returns the accuracy of a single guess. word is the word of the day 
# and guess is a guess from the user
def guess_accuracy(word, guess):
    # initialize accuracy
    accuracy = float()
    # for every letter in the word
    for i, ltr in enumerate(guess):
        # if the letter is in the word of the day
        if ltr in word:
            # if letter is in word of the day and in the same position of guess and word
            if ltr == word[i]:
                # add green score to accuracy (20%)
                accuracy += GREEN_SCORE
            # else letter is in the word but not in the same position
            else:
                # add green score to accuracy (10%)
                accuracy += YELLOW_SCORE
        # if letter is not in word, add not score
        else:
            continue
    # return accuracy of guess
    return accuracy
########################################################################################
########################################################################################
# returns the average accuracy of a users guesses. word is word of the day and guesses
# is a list of user guesses
def avg_accuracy(word:str, guesses:list):
    # initialize avg
    avg = float()
    # for each guess in guesses
    for guess in guesses:
        # add accuracy of guess to avg
        avg += guess_accuracy(word, guess)
    # return the average of accuracy
    return avg / len(guesses)
########################################################################################
