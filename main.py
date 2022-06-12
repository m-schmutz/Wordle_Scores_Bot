#!./env/bin/python3
from tracemalloc import start
import cv2
import time
import ansi
import wordle_image_processing as wip
import wordle_scoring as ws

def main():
    # Get the image
    image_path  = "./test_images/dark4.png"
    image       = cv2.imread(image_path)

    # Make sure it was read properly
    if image is None:
        quit("Error: Could not read image.")

    # Get guesses from image
    print( ansi.ansi("Analyzing...").italic(), end=' ' )
    start   = time.time()
    guesses = wip.get_guesses(image)
    end     = time.time()
    print( ansi.ansi("Finished in %.2fs"%(end - start)).italic() )

    # Pretty print scored game
    scored = ws.pretty_score_game(guesses, "CREAK")
    for guess in scored:
        print(guess)

    return

main()