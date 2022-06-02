#!./env/bin/python3
import cv2
import pytesseract
from constants import *
from ansi import *

_DEBUG_GEN_IMGS = True
_DEBUG_PRINT    = True

WHITE = [255, 255, 255]


### process_words:
############################################################################################
# Generates a list of words using positional image data and the image img_chars containing
# each word/guess.
def process_words(img_chars, cells_mask, cells, cell_width):
    if _DEBUG_PRINT: print("Processing...")

    # Local variable init
    words   = []                                    # The list of words we are generating
    offset  = int(cell_width * CELL_CHECK_FACTOR)   # The x/y-offset, in pixels

    #region Sort, Read, & Parse
    # We cannot gurantee that each character cell was produced in order from
    # left-to-right, so we will sort the cells by x/y-coordinates from top-to-bottom
    # and left-to-right, with priority to the former. This way we can ensure every
    # sequential subset of length WORD_LEN, starting at 0, contains the correct
    # characters. We then sort each subset from left-right, to produce the correct
    # word/guess made by the player.
    cells.sort( key=lambda c: (c[1], c[0]) )
    for i in range(len(cells) // 5):

        # Local variable init
        word        = ""                                    # The word of the current "row"
        cur_cells   = cells[ WORD_LEN*i : WORD_LEN*(i+1) ]  # The subset, or "row", of cells to look at

        #region Empty Row Check
        # Check the cells_mask at this row. We can stop generating words
        # if we know this row has blank cells. If any cells within a row
        # are blank, we know the entire row is also blank.
        cell        = cur_cells[0]
        x_offset    = cell[0] + offset
        y_offset    = cell[1] + offset

        if (not cells_mask[y_offset, x_offset]):
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


def filter_image(img):

    # Convert image to grayscale so we can use cv2.threshold() & cv2.findContours()
    img_grayscale = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if _DEBUG_GEN_IMGS: cv2.imwrite("debug_images_dump/img_grayscale.png", img_grayscale)

    # Generate cells_mask based on Wordle theme
    if list(img[0, 0]) == WHITE:
        # Generate a binary mask of the word cells
        # Pixels in range [200, 255] set to 0 (black), otherwise 1 (white)
        try: _, cells_mask = cv2.threshold(img_grayscale, 200, 255, cv2.THRESH_BINARY_INV)
        except Exception as e:  quit("> Error creating the cell mask:", e, "\n> Quitting...")
        if _DEBUG_GEN_IMGS: cv2.imwrite("debug_images_dump/cells_mask.png", cells_mask)

    else:
        # Generate a binary mask of the word cells
        # Pixels in range [50, 255] set to 1 (white), otherwise 0 (black)
        try: _, cells_mask = cv2.threshold(img_grayscale, 50, 255, cv2.THRESH_BINARY)
        except Exception as e:  quit("> Error creating the cell mask:", e, "\n> Quitting...")
        if _DEBUG_GEN_IMGS: cv2.imwrite("debug_images_dump/cells_mask.png", cells_mask)

    # Generate an inverted binary mask of the characters
    # Pixels in range [200, 255] set to 0 (black), otherwise 1 (white)
    try: _, img_chars = cv2.threshold(img_grayscale, 200, 255, cv2.THRESH_BINARY_INV)
    except Exception as e:  quit("> Error creating the character mask:", e, "\n> Quitting...")
    if _DEBUG_GEN_IMGS: cv2.imwrite("debug_images_dump/img_chars.png", img_chars)

    return img_chars, cells_mask



### _is_uniform:
############################################################################################
# Returns True when all items in the array are list-equivalent
#   - helper for _valid_margin()
def _is_uniform(array):
    array = array.tolist()
    val = array[0]
    for item in array:
        if item != val:
            return False
    return True

### _valid_margin:
############################################################################################
# We test the outermost edges of the image to disallow the image submission
# to be processed. By demanding a more structured input, we alleviate the amount
# of processing necessary.
#   - help for words_from_image()
def _valid_margin(img):

    # The dimensions of the image
    height  = img.shape[0]
    width   = img.shape[1]

    # Each edge/slice of the image (and no, i don't feel like getting rid of the redundant corner checks)
    if not _is_uniform( img[0, :]        ): return False    # North edge
    if not _is_uniform( img[:, width-1]  ): return False    # East edge
    if not _is_uniform( img[height-1, :] ): return False    # South edge
    if not _is_uniform( img[:, 0]        ): return False    # West edge

    return True
    
### words_from_image:
############################################################################################
# Given a cropped screenshot of a Worlde game, produces a list of the player's guesses.
def words_from_image(img):

    # Required Pre-processing Image Criteria
    if not _valid_margin(img):
        quit("> " + ANSI("Error: Your image needs to have a margin of space around the board!").red() + "\n> Quitting...")

    img_chars, cells_mask = filter_image(img)


    # Next, we will extract positional information from the contours produced by OpenCV.
    # Get the x/y-coordinate of each cell and their shared width
    try: cell_contours, _ = cv2.findContours(cells_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    except Exception as e:  quit("> Error generating the cell contours:", e, "\n> Quitting...")

    cells = []
    for contour in cell_contours:
        x, y, _, _ = cv2.boundingRect(contour)
        cells.append( (x, y) )
    
    if _DEBUG_GEN_IMGS:
        img_crosshairs = img.copy()
        leng = 10   # Crosshair radius
        for cell in cells:
            x = cell[0]
            y = cell[1]
            img_crosshairs[ y-leng:y+leng, x ] = (0,0,255)  # BGR
            img_crosshairs[ y, x-leng:x+leng ] = (0,0,255)
        cv2.imwrite("debug_images_dump/img_crosshairs.png", img_crosshairs)

    # Get the cells' width from an arbitrary cell contour (0th index, but can be any)
    _, _, cell_width, _ = cv2.boundingRect(cell_contours[0])


    # Finally, we can construct a list of the words using Tesseract
    return process_words(img_chars, cells_mask, cells, cell_width)




image_path = "./test_images/wordle_light_2.jpg"
image = cv2.imread(image_path)

if image is None:
    quit("> " + ANSI("Error: Could not read image.").red() + "\n> Quitting...")

words_from_image(image)