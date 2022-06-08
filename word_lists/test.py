#!./../env/bin/python3
from string import ascii_lowercase

def better(word:str, guess:str):
    avg = float()

def get_bloom(word:str):
    bf = [0] * 26
    for ltr in word:
        bf[ord(ltr) - 97] += 1
    return bf

word = 'trait'

guess = 'teiid'

d = dict()

w_bf = get_bloom(word)

g_bf = get_bloom(guess)

print(w_bf)

print(g_bf)

# maybe make a hashmap (class)
for ltr in ascii_lowercase:
    print(hash(ltr) % 26)

# loop through guess, remove letters that are not present in word of the say and keep track of other letters position.
