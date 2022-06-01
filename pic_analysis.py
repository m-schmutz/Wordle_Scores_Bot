#!./env/bin/python3
from random import uniform
import cv2
import pytesseract
import numpy as np
from constants import *

_DEBUG_GEN_IMGS = True
_DEBUG_PRINT    = False

### get_cell_offset:
# Returns the relative x/y-coordinate cell offset. This is used to for two reason:
#   1. Checking the cells_mask to validate a given cell
#   2. Slicing the image, removing whitespace around the given character
def get_cell_offset(width):
    return int(width * CELL_CHECK_FACTOR)

### process_words:
# Generates a list of words using positional image data and an image containing
# each word/guess, img_chars.
def process_words(img_chars, cells_mask, cells, cell_width):
    if _DEBUG_PRINT: print("Processing...")

    # Local variable init
    words   = []                            # The list of words we are generating
    offset  = get_cell_offset(cell_width)   # The x/y-offset, in pixels

    #region Sort, Read, & Parse
    # We cannot gurantee that each character cell was produced in order from
    # left-to-right, so we will sort the cells by x/y-coordinates from top-to-bottom
    # and left-to-right, with priority to the former. This way we can ensure every
    # sequential subset of length WORD_LEN, starting at 0, contains the correct
    # characters. We then sort each subset from left-right, to produce the correct
    # word/guess made by the player.
    cells.sort( key=lambda c: (c[1], c[0]) )
    for i in range(NUM_MAX_WORDS):

        # Local variable init
        word        = ""                                    # The word of the current "row"
        cur_cells   = cells[ WORD_LEN*i : WORD_LEN*(i+1) ]  # The subset, or "row", of cells to look at

        #region Empty Row Check
        # Check the cells_mask at this row. We can stop generating words
        # if we know this row has blank cells. If any cells within a row
        # are blank, we know the entire row is also blank.
        mask_check_cell = cur_cells[0]
        x_check         = mask_check_cell[0] + offset
        y_check         = mask_check_cell[1] + offset

        if (not cells_mask[y_check, x_check]):
            return words
        #endregion

        #region Sort Subset & Read Characters
        # Sort by x/y-coordinates, left-to-right
        cur_cells.sort( key=lambda c: c[0] )
        for cell in cur_cells:

            # Local variable init
            x = cell[0]                     # The x-coord of the cell's top-left point
            y = cell[1]                     # The y-coord of the cell's top-left point
            x_beg = x + offset              # The image's top slice bound
            y_beg = y + offset              # The image's left slice bound
            x_end = x + cell_width - offset # The image's lower slice bound
            y_end = y + cell_width - offset # The image's right slice bound

            # Slice the image and hand it off to Tesseract
            img_slice = img_chars[y_beg:y_end, x_beg:x_end]
            tess_output = pytesseract.image_to_string(img_slice, lang="eng", config=TESS_CONFIG)

            # Clean up the result and append it to the current word
            char = tess_output.strip()
            word += char
            if _DEBUG_PRINT: print(char, end='')
        #endregion

        # Add the word to our list
        words.append(word)
        if _DEBUG_PRINT: print('\n', end='')
    #endregion

    return words


def uniform_pixels(pixels):
    color = pixels[0]
    for pixel in pixels:
        if pixel != color:
            return False
    return True

def image_border_valid(img):
    dimensions  = img.shape
    height      = dimensions[0]
    width       = dimensions[1]
    edges       = {
        "left":     img[:, 0].tolist(),
        "top":      img[0, :].tolist(),
        "right":    img[:, width-1].tolist(),
        "bottom":   img[height-1, :].tolist()
    }

    uniform_left    = uniform_pixels( edges["left"] )
    uniform_top     = uniform_pixels( edges["top"] )
    uniform_right   = uniform_pixels( edges["right"] )
    uniform_bottom  = uniform_pixels( edges["bottom"] )

    return uniform_left and uniform_top and uniform_right and uniform_bottom
    


### words_from_image:
# Given a cropped screenshot of a Worlde game, produces a list of the player's guesses.
def words_from_image(img):

    if not image_border_valid(img):
        print("This image does not have enough whitespace around the World board!\nQuitting...")
        quit()

    #region Setup & Mask Generation
    ##### First, we will generate a mask for both the characters and the cells.

    # Convert image to grayscale so we can use cv2.threshold() & cv2.findContours()
    img_grayscale = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if _DEBUG_GEN_IMGS: cv2.imwrite("debug_images_dump/img_grayscale.png", img_grayscale)

    # Get inverted binary mask of the characters
    # Pixels in range [200, 255] set to 0 (black), otherwise 1 (white)
    _, img_chars = cv2.threshold(img_grayscale, 200, 255, cv2.THRESH_BINARY_INV)
    if _DEBUG_GEN_IMGS: cv2.imwrite("debug_images_dump/img_chars.png", img_chars)

    # Get binary mask of the character cells
    # Pixels in range [50, 255] set to 1 (white), otherwise 0 (black)
    _, cells_mask = cv2.threshold(img_grayscale, 50, 255, cv2.THRESH_BINARY)
    if _DEBUG_GEN_IMGS: cv2.imwrite("debug_images_dump/cells_mask.png", cells_mask)
    #endregion

    #region Milking the Contours
    ##### mommies milkers am i right
    ##### Next, we will extract positional information from the contours produced by OpenCV.

    # Get the x/y-coordinate of each cell and their shared width
    cells = []
    cell_contours, _ = cv2.findContours(cells_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for contour in cell_contours:
        x, y, _, _ = cv2.boundingRect(contour)
        cells.append( (x, y) )
    
    if _DEBUG_GEN_IMGS:
        img_crosshairs = img.copy()
        leng = 10           # Crosshair radius
        color = (0,0,255)   # BGR
        for cell in cells:
            x = cell[0]
            y = cell[1]
            img_crosshairs[y-leng:y+leng, x] = color
            img_crosshairs[y, x-leng:x+leng] = color
        cv2.imwrite("debug_images_dump/img_crosshairs.png", img_crosshairs)

    # Get the cells' width from an arbitrary cell contour (0th index, but can be any)
    _, _, cell_width, _ = cv2.boundingRect(cell_contours[0])
    #endregion

    # Construct a list of the words using Tesseract
    return process_words(img_chars, cells_mask, cells, cell_width)

### main:
# Grab a Wordle game screenshot and print the words/guesses.
def main():
    image = cv2.imread("./test_images/wordle_light_2.jpg")
    words = words_from_image(image)
    if _DEBUG_PRINT:
        print("Done!")
        print(words)

main()