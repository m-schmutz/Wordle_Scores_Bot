# Tesseract Manual: https://github.com/tesseract-ocr/tesseract/blob/main/doc/tesseract.1.asc

import cv2
import numpy as np
import pytesseract
from multiprocessing import Pool
from psutil import cpu_count


# CONSTANTS ################################################################################
############################################################################################
_DEBUG_GEN_IMGS     = False
_DEBUG_PRINT        = True

#region Tesseract Config Constants
_ORIG:int           = 0     # "Original Tesseract only."
_NEURAL_LSTM:int    = 1     # "Neural nets LSTM only."
_TESS_LSTM:int      = 2     # "Tesseract + LSTM."
_OEM_DEFAULT:int    = 3     # "Default, based on what is available."
_OSD:int            = 0     # "Orientation and script detection (OSD) only."
_AUTO_OSD:int       = 1     # "Automatic page segmentation with OSD."
_AUTO:int           = 2     # "Automatic page segmentation, but no OSD, or OCR. (not implemented)"
_PSM_DEFAULT:int    = 3     # "Fully automatic page segmentation, but no OSD. (Default)"
_SINGLE_COL:int     = 4     # "Assume a single column of text of variable sizes."
_SINGLE_VBLOCK:int  = 5     # "Assume a single uniform block of vertically aligned text."
_SINGLE_BLOCK:int   = 6     # "Assume a single uniform block of text."
_SINGLE_LINE:int    = 7     # "Treat the image as a single text line."
_SINGLE_WORD:int    = 8     # "Treat the image as a single word."
_CIRCLE:int         = 9     # "Treat the image as a single word in a circle."
_SINGLE_CHAR:int    = 10    # "Treat the image as a single character."
_SPARSE:int         = 11    # "Sparse text. Find as much text as possible in no particular order."
_SPARSE_OSD:int     = 12    # "Sparse text with OSD."
_RAW_LINE:int       = 13    # "Raw line. Treat the image as a single text line, bypassing hacks that are Tesseract-specific."
_WHITELIST:str      = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
#endregion

CELL_WIDTH_FACTOR   = 0.2   # This helps Tesseract produce more consitent and correct characters
CONFIG              = f'--oem {_OEM_DEFAULT} --psm {_SINGLE_CHAR} -c tessedit_char_whitelist={_WHITELIST}'
GUESS_LENGTH        = 5

BLURS               = [ (3,3), (5,5), (3,5), (5,3), (1,5), (5,1) ]  # idk seemed to resolve all misreads i saw NOTE output all images of given test case to see whats happening
MAX_THRESH          = 255               # Maximum grayscale pixel value
THEME_THRESH        = MAX_THRESH // 2   # Comparison value to choose theme code path
BOTH_MASK_THRESH    = 200               # Used for Light theme
CELLS_MASK_THRESH   = 50                # Used for Dark theme
CHARS_MASK_THRESH   = 200               # Used for Dark theme


# INTERNAL FUNCTIONS #######################################################################
############################################################################################

# _try_blurs: ______________________________________________________________________________
# Attempts to extract a character from an image slice using a variety of different blur
# factors, BLUR_FACTORS. If it returns None, no character could be read by Tesseract.
def _try_blurs(img):

    for blur in BLURS:
        tess_source = cv2.blur( img, blur )
        char = pytesseract.image_to_string( tess_source, lang="eng", config=CONFIG ).strip()
        if char != "":
            return char

    return None

# _process_words: __________________________________________________________________________
# Generates a list of words using positional image data and the image img_chars containing
# each word/guess.
def _process_words(img_chars, cells_mask, cells, cell_width):

    offset = int(cell_width * CELL_WIDTH_FACTOR) # The x/y-offset, in pixels

    # Create a sorted list of each character image.
    # It's size will always be a multiple of WORD_LEN.
    # - We cannot gurantee that each character cell was produced in order from
    #   left-to-right, so we will sort the cells by x/y-coordinates from top-to-bottom
    #   and left-to-right, with priority to the former. This way we can ensure every
    #   sequential subset of length WORD_LEN, starting at 0, contains the correct
    #   characters. We then sort each subset from left-right, to produce the correct
    #   word/guess made by the player.
    cell_imgs = []
    num_rows = len(cells) // GUESS_LENGTH
    cells.sort( key=lambda c: (c[1], c[0]) )
    for i in range(num_rows):
        beg        = i * GUESS_LENGTH
        row_cells  = cells[beg : beg + GUESS_LENGTH]

        # If any cell mask in the current row is 0, we know there are no more guesses
        # and can stop obtaining images to read
        sample_cell = row_cells[0]
        if not cells_mask[sample_cell[1] + offset, sample_cell[0] + offset]:
            break
        
        # Sort the row
        row_cells.sort( key=lambda c: c[0] )
        for cell in row_cells:
            # Top-left coordinate of cell
            x = cell[0]
            y = cell[1]

            # Append image of the given character to list
            inverse_offset = cell_width - offset
            cell_imgs.append(img_chars[(y + offset):(y + inverse_offset), (x + offset):(x + inverse_offset)])

    # Create multiple processes to process character images quickly
    # using half as many cores seems to be the quickest. perhaps tesseract reserves a core itself?
    # raw_num_cores = cpu_count()
    # num_cores     = raw_num_cores // 2
    # if _DEBUG_PRINT: print(f"Detected {raw_num_cores} cores, using {num_cores}.")
    num_phys_cores  = cpu_count(logical=False)
    if _DEBUG_PRINT: print(f"Detected {num_phys_cores} physical core{'s' if num_phys_cores > 1 else ''}")
    chars           = Pool(num_phys_cores).map(_try_blurs, cell_imgs)

    # Reconstruct the words from the list of characters read by Tesseract
    num_rows = len(chars) // GUESS_LENGTH
    words    = []
    for i in range(num_rows):
        beg = i * GUESS_LENGTH
        words.append("".join(chars[beg:(beg + GUESS_LENGTH)]))
    if _DEBUG_PRINT: print("word list =", words)

    return words

# _is_uniform: _____________________________________________________________________________
# Returns True when all items in the array are list-equivalent
def _is_uniform(arr:list):
    sample = arr[0]
    for elem in arr:
        if elem != sample:
            return False
    return True

# _validate_margin: ________________________________________________________________________
# We test the outermost edges of the image to disallow the image submission
# to be processed. By demanding a more structured input, we alleviate the amount
# of processing necessary.
def _validate_margin(img:list):

    # Each edge/slice of the image (and no, i don't feel like getting rid of the redundant corner checks)
    height     = img.shape[0]
    width      = img.shape[1]
    img_north  = img[0, :]
    img_east   = img[:, width-1]
    img_south  = img[height-1, :]
    img_west   = img[:, 0]

    # Check each edge
    if not _is_uniform(img_north): return False
    if not _is_uniform(img_east):  return False
    if not _is_uniform(img_south): return False
    if not _is_uniform(img_west):  return False
    if _DEBUG_GEN_IMGS:
        cv2.imwrite("debug_images_dump/top_edge.png", img_north)
        cv2.imwrite("debug_images_dump/left_edge.png", img_east)
        cv2.imwrite("debug_images_dump/bottom_edge.png", img_south)
        cv2.imwrite("debug_images_dump/right_edge.png", img_west)

    return True

# _get_masks: ______________________________________________________________________________
# Generate a mask for both the character cells and the characters themselves.
def _gen_masks(img:list):

    # Convert image to grayscale so we can use cv2.threshold() & cv2.findContours()
    img_grayscale = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Sample image to determine theme
    light_theme:bool = all( (val >= THEME_THRESH) for val in img[0, 0] )

    # Generate the cell/character masks based theme
    if light_theme:
        # Light Theme
        _, cells_mask_inv       = cv2.threshold(img_grayscale, BOTH_MASK_THRESH, MAX_THRESH, cv2.THRESH_BINARY)
        chars_mask = cells_mask = cv2.bitwise_not(cells_mask_inv)
    else:
        # Dark Theme
        _, cells_mask = cv2.threshold(img_grayscale, CELLS_MASK_THRESH, MAX_THRESH, cv2.THRESH_BINARY)
        _, chars_mask = cv2.threshold(img_grayscale, CHARS_MASK_THRESH, MAX_THRESH, cv2.THRESH_BINARY_INV)

    # Make sure the image was cropped correctly
    if not _validate_margin(cells_mask):
        quit("Error: Image needs to have a margin of space around the board!")

    if _DEBUG_GEN_IMGS:
        cv2.imwrite("debug_images_dump/cells_mask.png", cells_mask)
        cv2.imwrite("debug_images_dump/chars_mask.png", chars_mask)
        cv2.imwrite("debug_images_dump/img_grayscale.png", img_grayscale)

    return chars_mask, cells_mask



# USER FUNCTIONS ###########################################################################
############################################################################################

# get_guesses: _____________________________________________________________________________
# Given a cropped screenshot of a Worlde game, produces a list of the player's guesses.
def get_guesses(img_bytes:list):

    # Convert bytes image to readable format for OpenCV
    nparr = np.frombuffer(img_bytes, np.uint8)
    img   = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # Generate a mask of the cells and characters
    chars_mask, cells_mask = _gen_masks(img)

    # Next, we will extract information from the contours produced by OpenCV.
    cell_contours, _    = cv2.findContours(cells_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    _, _, cell_width, _ = cv2.boundingRect(cell_contours[0])

    # Get the x/y-coordinate of each cell and their shared width
    cells = []
    for contour in cell_contours:
        x, y, _, _ = cv2.boundingRect(contour)
        cells.append((x, y))

    if _DEBUG_GEN_IMGS:
        img_cell_contours = cv2.drawContours(img.copy(), cell_contours, -1, (0,0,255))
        cv2.imwrite('debug_images_dump/img_contours.png', img_cell_contours)

        img_crosshairs = img.copy()
        radius = cell_width // 20  # arbitrary value
        for cell in cells:
            x = cell[0]
            y = cell[1]
            img_crosshairs[(y - radius):(y + radius), x] = (0,0,255)
            img_crosshairs[y, (x - radius):(x + radius)] = (0,0,255)
        cv2.imwrite("debug_images_dump/img_crosshairs.png", img_crosshairs)

    # Finally, we can construct a list of the words using Tesseract
    return _process_words(chars_mask, cells_mask, cells, cell_width)
