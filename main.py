#!./env/bin/python3
import cv2
import time
import ansi
import wordle_image_processing as wip
import wordle_scoring as ws

_DEBUG_PRINT = False

def main():
    # Get the image
    image_path  = "./test_images/dark4.png"
    image       = cv2.imread(image_path)

    # Make sure it was read properly
    if image is None:
        quit("Error: Could not read image.")

    # Get guesses from image
    if _DEBUG_PRINT:
        print(ansi.ansi("Analyzing image...").italic(), end=' ')
        start   = time.time()
        guesses = wip.get_guesses(image)
        end     = time.time()
        print(ansi.ansi("Finished in %.2fs"%(end - start)).italic())
    else:
        guesses = wip.get_guesses(image)

    # Score the game
    scores = ws.score_game(guesses, "CREAK")

    # Pretty print the game
    pretty = ws.pretty(guesses, scores)
    for p in pretty:
        print(p)

    return 0

main()