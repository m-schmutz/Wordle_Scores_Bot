"""# Tesseract Manual: https://github.com/tesseract-ocr/tesseract/blob/main/doc/tesseract.1.asc
from typing import Any
import cv2
from cv2 import contourArea
from numpy import frombuffer, square, uint8
from pytesseract import pytesseract, image_to_string
from multiprocessing import Pool
from psutil import cpu_count

pytesseract.tesseract_cmd = '/usr/bin/tesseract'

### CONSTANTS #################################################################################

_DEBUG_GEN_IMGS     = False
_DEBUG_PRINT        = True
_TESS_ORIG          = 0     # "Original Tesseract only."
_TESS_NEURAL_LSTM   = 1     # "Neural nets LSTM only."
_TESS_TESS_LSTM     = 2     # "Tesseract + LSTM."
_TESS_OEM_DEFAULT   = 3     # "Default, based on what is available."
_TESS_OSD           = 0     # "Orientation and script detection (OSD) only."
_TESS_AUTO_OSD      = 1     # "Automatic page segmentation with OSD."
_TESS_AUTO          = 2     # "Automatic page segmentation, but no OSD, or OCR. (not implemented)"
_TESS_PSM_DEFAULT   = 3     # "Fully automatic page segmentation, but no OSD. (Default)"
_TESS_SINGLE_COL    = 4     # "Assume a single column of text of variable sizes."
_TESS_SINGLE_VBLOCK = 5     # "Assume a single uniform block of vertically aligned text."
_TESS_SINGLE_BLOCK  = 6     # "Assume a single uniform block of text."
_TESS_SINGLE_LINE   = 7     # "Treat the image as a single text line."
_TESS_SINGLE_WORD   = 8     # "Treat the image as a single word."
_TESS_CIRCLE        = 9     # "Treat the image as a single word in a circle."
_TESS_SINGLE_CHAR   = 10    # "Treat the image as a single character."
_TESS_SPARSE        = 11    # "Sparse text. Find as much text as possible in no particular order."
_TESS_SPARSE_OSD    = 12    # "Sparse text with OSD."
_TESS_RAW_LINE      = 13    # "Raw line. Treat the image as a single text line, bypassing hacks that are Tesseract-specific."

WHITELIST           = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
CELL_WIDTH_FACTOR   = 0.2   # This helps Tesseract produce more consitent and correct characters
CONFIG              = f'--oem {_TESS_OEM_DEFAULT} --psm {_TESS_SINGLE_CHAR} -c tessedit_char_whitelist={WHITELIST}'
GUESS_LENGTH        = 5
BLURS               = [ (3,3), (5,5), (3,5), (5,3), (1,5), (5,1) ]  # idk seemed to resolve all misreads i saw NOTE output all images of given test case to see whats happening
MAX_THRESH          = 255               # Maximum grayscale pixel value
THEME_THRESH        = MAX_THRESH // 2   # Comparison value to choose theme code path
BOTH_MASK_THRESH    = 200               # Used for Light theme
CELLS_MASK_THRESH   = 50                # Used for Dark theme
CHARS_MASK_THRESH   = 200               # Used for Dark theme

### INTERNAL USE ##############################################################################

# _try_blurs: _____________________________________________________________________________
# Attempts to extract a character from an image slice using a variety of different blur
# factors, BLUR_FACTORS. If it returns None, no character could be read by Tesseract.
def _try_blurs(img):
    for blur in BLURS:
        blurred_img = cv2.blur( img, blur )
        char:str = image_to_string( blurred_img, lang="eng", config=CONFIG ).strip()
        if char in WHITELIST:
            return char.lower()
    return None

# _process_words: _________________________________________________________________________
# Generates a list of words using positional image data and the image img_chars containing
# each word/guess.
def _process_words(img_chars, cells_mask, cells:list, cell_width) -> 'list[str]':

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
    num_phys_cores = cpu_count(logical=False)
    if _DEBUG_PRINT: print(f'Detected {num_phys_cores} physical core{"s" if num_phys_cores > 1 else ""}')
    chars = Pool(num_phys_cores).map(_try_blurs, cell_imgs)

    # Reconstruct the words from the list of characters read by Tesseract
    num_rows = len(chars) // GUESS_LENGTH
    words = []
    for i in range(num_rows):
        beg = i * GUESS_LENGTH
        words.append(''.join(chars[beg:(beg + GUESS_LENGTH)]))
    if _DEBUG_PRINT: print('word list =', words)

    return words

# _is_uniform: ____________________________________________________________________________
# Returns True when all items in the array are list-equivalent
def _is_uniform(arr:list):
    sample = arr[0]
    for elem in arr:
        if elem != sample:
            return False
    return True

# _validate_margin: _______________________________________________________________________
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

# _get_masks: _____________________________________________________________________________
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

### EXTERNAL USE ##############################################################################

# image_to_guess_list: ____________________________________________________________________
# Given a cropped screenshot of a Worlde game, produces a list of the player's guesses.
def image_to_guess_list(bytes: bytes) -> 'list[str]':

    # Convert bytes image to readable format for OpenCV
    nparr = frombuffer(bytes, uint8)
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

"""

from random import randint
from re import L
import cv2
import numpy as np
import time
import ansi
import multiprocessing as mp
from psutil import cpu_count


def timer(func):
    def _inner(*args, **kwargs):
        beg = time.perf_counter()
        ret = func(*args, **kwargs)
        end = time.perf_counter()
        print(f'[{end-beg:.06f}s] {func.__name__}:')
        return ret
    return _inner


""" The following information was gathered directly from https://www.nytimes.com/games/wordle/index.html.
FILE: wordle.de5cb286f0d33d9aff3bbedee6ec2ae37d46994f.js
PURPOSE: Set the width and height of the board on window.resize
    "var Ie=5"......at (1, 114566)
    "var Le=6"......at (1, 114566)
    "var So=350"....at (1, 157748)
    "function e() {
        var e, t=l.current, n=c.current;
        t&&n&&(
            e = Math.min(
                Math.floor(t.clientHeight*(Le/Ie)),
                So),
            t = Math.floor(e/Le)*Ie,n.style.width="".concat(e,"px"),n.style.height="".concat(t,"px")
        )
    }"..............at (1, 157887)
"""

COLS = 5
# ROWS = 6

# these should be treated as ratios to one-another
# GRID_GAP    = 5
# GRID_WIDTH  = 330
# GRID_HEIGHT = 400

# BG          = 0xffffff  # :root/--color-tone-7
# BG_DARK     = 0x121213  # .dark/--color-tone-7
# GREEN       = 0x6aaa64  # :root/--green
# GREEN_DARK  = 0x538d4e  # :root/--darkendgreen
# YELLOW      = 0xc9b458  # :root/--yellow
# YELLOW_DARK = 0xb59f3b  # :root/--darkendyellow
# GRAY        = 0x787c7e  # :root/--color-tone-2
# GRAY_DARK   = 0x3a3a3c  # .dark/--color-tone-4
# BORDER      = 0xd3d6da
# BORDER_DARK = 0x3a3a3c

class WordleImageProcessor:
    def __init__(self, image: bytes, *, area_margin: int = 50) -> None:
        self.image: cv2.Mat = cv2.imdecode(np.frombuffer(image, np.uint8), cv2.IMREAD_COLOR)
        self.grayscale: cv2.Mat = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        self.area_margin: int = area_margin

        self.alphabet: str = 'abcdefghijklmnopqrstuvwxyz'
        self.alphabet_masks: list[cv2.Mat] = list(cv2.imread(f'lib/alphabet_masks/{char}.png', cv2.IMREAD_UNCHANGED)
            for char in self.alphabet)

        self.char_masks: list[cv2.Mat] = []
        self.cells_mask: cv2.Mat = None
        self.cell_contours: list[np.ndarray] = []
        self.cellsize: int = 0


        # Generate a list of contours of the game-board's cells.
        _, self.cells_mask = cv2.threshold(self.grayscale, 50, 255, cv2.THRESH_BINARY) # ASSUMES DARK THEME
        contours, _ = cv2.findContours(
            image = self.cells_mask,
            mode = cv2.RETR_EXTERNAL,
            method = cv2.CHAIN_APPROX_SIMPLE)

        ############# TODO: Programatically find the board!!! ################
        self.cell_contours = self.square_cells(contours)
        ############# Assuming we have ONLY the cell contours ##############

        ### Setup letter masks
        # Resize the masks to fit self's image or vice versa, if necessary
        # [Preferalbe resize interpolation methods](https://docs.opencv.org/4.x/da/d6e/tutorial_py_geometric_transformations.html)
        _, _, self.cellsize, _ = cv2.boundingRect(self.cell_contours[0])
        alphabet_masksize = 155
        if self.cellsize != alphabet_masksize:
            if self.cellsize < alphabet_masksize:
                self.alphabet_masks = list(cv2.resize(m, (self.cellsize, self.cellsize), interpolation=cv2.INTER_AREA)
                    for m in self.alphabet_masks)
            else:
                ratio = alphabet_masksize / self.cellsize
                height, width = map(lambda a: int(a*ratio), self.grayscale.shape[:2])
                self.grayscale = cv2.resize(self.grayscale, (width, height), interpolation=cv2.INTER_LINEAR)
                quit('IMPLEMENT THIS HAHA')

        ### Generate a list of masks of the guessed letters.
        # Because cv2.findContours() works right-to-left bottom-up, we 
        # reverse the list to maintain indexing order across this class.
        midpoint = self.cellsize // 2
        _, chars_mask = cv2.threshold(self.grayscale, 200, 255, cv2.THRESH_BINARY)
        cv2.imwrite('chars_mask.png', chars_mask)
        for (x, y), _, _, _ in reversed(self.cell_contours):
            if not self.cells_mask[y+midpoint, x+midpoint]:
                break
            self.char_masks.append(chars_mask[y:y+self.cellsize, x:x+self.cellsize])

    def countNonZeroAND(self, m1, m2) -> int:
        return int(cv2.countNonZero(cv2.bitwise_and(m1, m2)))
    
    def countNonZeroXOR(self, m1, m2) -> int:
        return int(cv2.countNonZero(cv2.bitwise_xor(m1, m2)))

    @timer
    def square_cells(self, contours:'list[np.ndarray]'):
        SQUARE_THRESH:int = 2   # the highest difference in width-height to permit
        SQUARE_ARRSIZE:int = 8  # 4 pairs of x/y-coords
        squares = list()
        for c in contours:
            # disregard any contours that are not a quadrilateral
            if c.size != SQUARE_ARRSIZE:
                continue

            # disregard any contour whose bounding box is not approximately a square
            _, _, w, h = cv2.boundingRect(c)
            if abs(w - h) > SQUARE_THRESH:
                continue

            squares.append(c)
        return np.squeeze(squares)

    def determine_char(self, mask: cv2.Mat, use_margin: bool = False) -> str:
        """Compare the provided mask against all alphabetic letters to determine the best candidate.
        
        ---
        ## Parameters
        
        mask : cv2.Mat
            A single user character mask.
            
        use_margin : bool
            Determines whether or not to use the error margin method. When this is True, an assertion
            error may be raised if a candidate could not be chosen. Higher error margin values are
            more lenient."""
        mask_count = cv2.countNonZero(mask)
        index = None

        if use_margin:
            '''This technique uses a margin of error.

            The intersection will be calculated for every character in the alphabet. On
            the other hand, the difference will only be calculated if the intersection's
            area is within range of `mask`'s area.
            
            This will generally be faster (1-2ms on a full board), as we only need to
            traverse the list once (i.e. no sorting) and we do not calculate the difference
            every time. The downside is that it relies on an arbitrary error margin that
            can be affected by the image quality. The other technique is unaffected by this.'''
            lowest_diff = np.inf
            for i, amask in enumerate(self.alphabet_masks):
                if abs(self.countNonZeroAND(mask, amask) - mask_count) <= self.area_margin:
                    diff = self.countNonZeroXOR(mask, amask)
                    if diff < lowest_diff:
                        lowest_diff = diff
                        index = i
            if index == None:
                raise AssertionError(ansi.red('Could not determine the letter. Try increasing the error margin or disabling use_margin.'))
        else:
            '''This technique relies on built in `sort` method.
            
            The intersection and difference is calculated for every character in the
            alphabet. Instead of storing the intersection value, we store the displacement
            from `mask`'s area to it's area. In doing so, we can copy and sort the completed
            list by magnitude -- first by the difference, then by the displacement. As a
            result, the first element of the list will yield the tuple of interest. We can
            then refer to the original list to find it's index.'''
            mask_results = list(
                (self.countNonZeroXOR(mask, amask),
                    abs(self.countNonZeroAND(mask, amask) - mask_count))
                # (abs(self.__andCount(mask, amask) - mask_count),
                #     self.__xorCount(mask, amask))
                for amask in self.alphabet_masks)
            s = sorted(mask_results)
            index = mask_results.index(s[0])
            char = self.alphabet[index]

        return char

    @timer
    def get_guesses(self) -> 'list[str]':
        chars = list(self.determine_char(mask)
            for mask in self.char_masks)

        return list(''.join(chars[i:i+COLS])
            for i in range(0, len(self.char_masks), COLS))



if __name__ == '__main__':
    fd = open('wordle-game-1.png', 'rb')
    image_bytes = fd.read()
    fd.close()
    imgproc = WordleImageProcessor(image_bytes)
    guesses = imgproc.get_guesses()
    print('Guesses:', end=' "')
    print(*guesses, sep='", "', end='"\n')

    # # Create alphabet masks without padding.
    # for a,m in zip(imgproc.alphabet, imgproc.alphabet_masks):
    #     #should only be one contour
    #     contours, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    #     x,y,w,h = cv2.boundingRect(contours[0])
    #     print('w=',w,'h=',h)

    #     slce = m[y:y+h,x:x+w]
    #     cv2.imwrite(f'lib/alphabet_masks_new/{a}.png', slce)
