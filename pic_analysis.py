#!./env/bin/python3
import cv2
import pytesseract
from constants import *
from ansi import *

_DEBUG_GEN_IMGS = False
_DEBUG_PRINT    = False

#region INTERNAL FUNCTIONS
### _try_blurs:
############################################################################################
# Attempts to extract a character from an image slice using a variety of different blur
# factors, BLUR_FACTORS. If it returns None, no character could be read by Tesseract.
def _try_blurs(img):

    for bf in BLUR_FACTORS:
        tess_source = cv2.blur( img, bf )
        tess_output = pytesseract.image_to_string( tess_source, lang="eng", config=TESS_CONFIG )
        char = tess_output.strip()
        if char != "":
            return char

    return None

### _process_words:
############################################################################################
# Generates a list of words using positional image data and the image img_chars containing
# each word/guess.
def _process_words(img_chars, cells_mask, cells, cell_width):
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
    for i in range( len(cells) // 5 ):

        # Local variable init
        word        = ""                                            # The word of the current "row"
        cur_cells   = cells[ WORD_LEN * i : WORD_LEN * (i + 1) ]    # The subset, or "row", of cells to look at

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

            # Slice the image and try a handful of blur parameters on it
            img_char = img_chars[ y_beg:y_end, x_beg:x_end ]
            char = _try_blurs(img_char)
            if char == None:
                cv2.imwrite("./debug_images_dump/bad_char.png", img_char)
                quit("Could not resolve a character for image \"/debug_images_dump/bad_char.png\"")

            word += char
            if _DEBUG_PRINT: print(char, end='')
        #endregion

        # Add the word to our list
        words.append(word)
        if _DEBUG_PRINT: print('\n', end='')
    #endregion

    return words

### _is_uniform:
############################################################################################
# Returns True when all items in the array are list-equivalent
#   - helper for _valid_margin()
def _is_uniform(array):
    array = array.tolist()
    sample = array[0]
    for element in array:
        if element != sample:
            return False
    return True

### _validate_margin:
############################################################################################
# We test the outermost edges of the image to disallow the image submission
# to be processed. By demanding a more structured input, we alleviate the amount
# of processing necessary.
def _validate_margin(img):

    # The dimensions of the image
    height  = img.shape[0]
    width   = img.shape[1]

    # Each edge/slice of the image (and no, i don't feel like getting rid of the redundant corner checks)
    if not _is_uniform( img[0, :] ): return False           # North edge
    if _DEBUG_GEN_IMGS: cv2.imwrite("debug_images_dump/top_edge.png", img[0, :])
    
    if not _is_uniform( img[:, width-1] ): return False     # East edge
    if _DEBUG_GEN_IMGS: cv2.imwrite("debug_images_dump/left_edge.png", img[:, width-1])
    
    if not _is_uniform( img[height-1, :] ): return False    # South edge
    if _DEBUG_GEN_IMGS: cv2.imwrite("debug_images_dump/bottom_edge.png", img[height-1, :])
    
    if not _is_uniform( img[:, 0] ): return False           # West edge
    if _DEBUG_GEN_IMGS: cv2.imwrite("debug_images_dump/right_edge.png", img[:, 0])

    return True

### _get_masks:
############################################################################################
# Generate a mask for both the character cells and the characters themselves.
def _get_masks(img):

    # Convert image to grayscale so we can use cv2.threshold() & cv2.findContours()
    img_grayscale = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    sample_pixel = img[0, 0]
    light_theme = all( val >= 100 for val in sample_pixel )

    # Generate the cells and characters masks
    # Light Theme
    if light_theme:
        _, cells_mask_inv = cv2.threshold(img_grayscale, 200, 255, cv2.THRESH_BINARY)
        chars_mask = cells_mask = cv2.bitwise_not(cells_mask_inv)
    # Dark Theme
    else:
        _, cells_mask = cv2.threshold(img_grayscale, 50, 255, cv2.THRESH_BINARY)
        _, chars_mask = cv2.threshold(img_grayscale, 200, 255, cv2.THRESH_BINARY_INV)

    # Make sure the image was cropped correctly
    if not _validate_margin(cells_mask):
        quit("> " + ANSI("Error: Your image needs to have a margin of space around the board!").red() + "\n> Quitting...")

    if _DEBUG_GEN_IMGS:
        cv2.imwrite("debug_images_dump/cells_mask.png", cells_mask)
        cv2.imwrite("debug_images_dump/chars_mask.png", chars_mask)
        cv2.imwrite("debug_images_dump/img_grayscale.png", img_grayscale)

    return chars_mask, cells_mask
#endregion

# Functions for external use:
### words_from_image:
############################################################################################
# Given a cropped screenshot of a Worlde game, produces a list of the player's guesses.
def words_from_image(img):

    # Generate a mask of the cells and characters
    chars_mask, cells_mask = _get_masks(img)

    # Next, we will extract information from the contours produced by OpenCV.
    cell_contours, _ = cv2.findContours(cells_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    _, _, cell_width, _ = cv2.boundingRect(cell_contours[0])

    # Get the x/y-coordinate of each cell and their shared width
    cells = []
    for contour in cell_contours:
        x, y, _, _ = cv2.boundingRect(contour)
        cells.append( (x, y) )

    if _DEBUG_GEN_IMGS:
        img_contours = cv2.drawContours(img.copy(), cell_contours, -1, (0,0,255))
        cv2.imwrite('debug_images_dump/img_contours.png', img_contours)

        img_crosshairs = img.copy()
        leng = cell_width // 20
        for cell in cells:
            x = cell[0]
            y = cell[1]
            img_crosshairs[ y-leng:y+leng, x ] = (0,0,255)  # BGR
            img_crosshairs[ y, x-leng:x+leng ] = (0,0,255)
        cv2.imwrite("debug_images_dump/img_crosshairs.png", img_crosshairs)

    # Finally, we can construct a list of the words using Tesseract
    return _process_words(chars_mask, cells_mask, cells, cell_width)



# image_path = "./test_images/light1.png"
# image = cv2.imread(image_path)
# if image is None:
#     quit("> " + ANSI("Error: Could not read image.").red() + "\n> Quitting...")
# words_from_image(image)

# for i in range(1, 5):
#     image = cv2.imread(f"./test_images/dark{i}.png")
#     words_from_image(image)
#     image = cv2.imread(f"./test_images/light{i}.png")
#     words_from_image(image)