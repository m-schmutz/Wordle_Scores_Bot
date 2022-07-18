"""
# Tesseract Manual: https://github.com/tesseract-ocr/tesseract/blob/main/doc/tesseract.1.asc
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

from typing import Any
import cv2
import numpy as np
import time
# from collections import Counter
# from math import sqrt

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

GRID_NUM_COLS       = 5
GRID_NUM_ROWS       = 6
GRID_GAP            = 5
GRID_MAX_WIDTH      = 350
GRID_MAX_HEIGHT     = 420
GRID_MAX_CELL_SIZE  = 62
GRID_PADDING        = 10

BG          = 0xffffff  # :root/--color-tone-7
BG_DARK     = 0x121213  # .dark/--color-tone-7
GREEN       = 0x6aaa64  # :root/--green
GREEN_DARK  = 0x538d4e  # :root/--darkendgreen
YELLOW      = 0xc9b458  # :root/--yellow
YELLOW_DARK = 0xb59f3b  # :root/--darkendyellow
GRAY        = 0x787c7e  # :root/--color-tone-2
GRAY_DARK   = 0x3a3a3c  # .dark/--color-tone-4
BORDER      = 0xd3d6da
BORDER_DARK = 0x3a3a3c

# class Contours

class WordleImageProcessor:
    def __init__(self, image: bytes, *, error_margin: int = 2) -> None:
        self._alphabet = 'abcdefghijklmnopqrstuvwxyz'
        self.image: np.ndarray  = cv2.imdecode(np.frombuffer(image, np.uint8), cv2.IMREAD_COLOR)
        self.error_margin: int  = error_margin
        self._generate_data()

    # if length2 in [length1-error_margin, length1+error_margin] -> True
    # otherwise -> False
    def _within_error_margin(self, /, length1: int, length2: int, error_margin: int) -> bool:
        # bottom half of error margin
        if length1 < length2 - error_margin:
            return False
        
        # top half of error margin
        if length1 > length2 + error_margin:
            return False

        return True

    # Returns all contours that are squares (EFFECTED BY ERROR_MARGIN)
    def _square_contours(self, contours: 'list[np.ndarray]') -> 'list[np.ndarray]':
        square_contours: list[np.ndarray] = []
        for contour in contours:
            # disregard any contours that are not a quadrilateral
            if len(contour) != 4:
                continue
            
            # disregard any contour whose bounding box is not ~square
            _, _, w, h = cv2.boundingRect(contour)
            if not self._within_error_margin(w, h, self.error_margin):
                continue

            # keep all ~square contours
            square_contours.append(np.squeeze(contour))

        # print(f'Keeping {len(square_contours)}...')
        return square_contours

    #region unused functions
        # Tries to find the character cell contours and returns them in a list.
    # def find_cell_contours(self) -> 'list[np.ndarray]':
        # # reduce the number of contours by limiting their shape to be strictly squares, within ERROR_MARGIN
        # _, mask = cv2.threshold(self.grayscale_mat, 50, 255, cv2.THRESH_BINARY)
        # contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # square_contours = self._square_contours(contours)

        #region add optional method By Grid:
        # board_contour_coords = []
        # streak = []
        # for coord in contour_coords:

        #     if len(streak) == 5:
        #         print('potential game board row found!')
        #         board_contour_coords += streak
        #         streak = [coord]
        #         continue

        #     elif len(streak) == 0:
        #         streak.append(coord)
        #         continue

        #     # if the current y-coord equals the previous y-coord,
        #     # add coord to streak. if streak gets to length 5, we
        #     # have found 5 contours on the same y-level in a row.
        #     # this is likely to be a row from the game board, but we need
        #     # to compare x-coords as well to be sure.
        #     print(f'cur-y: {coord[1]}, prev-y: {streak[-1][1]}')
        #     if coord[1] == streak[-1][1]:
        #         streak.append(coord)
        #         continue

        #     streak = [coord]

        # # print(contour_coords)
        # print(board_contour_coords)
        # # xs = Counter([x for (x, _) in board_contour_coords])
        # ys = Counter([y for (_, y) in board_contour_coords])
        # # print(xs)
        # print(ys)
        # quit()
        #endregion

        #region By Area
        # areas = [cv2.contourArea(c) for c in square_contours]

        # # tally the number of contours with unique areas
        # counter = Counter(areas)
        # print(counter)

        # # grab the largest area
        # max_area = counter.most_common()[0][0]
        # print(max_area)

        # # take the sqrt -> should be an integer since the majority of the cell contours are perfect squares
        # sr = sqrt(max_area)
        # print(sr)

        # # assuming we successfully obtained the largest width, determine the
        # # smallest acceptable area for a cell contour given ERROR_MARGIN. And...
        # thresh = (sr - self.error_margin)**2
        # print(thresh)

        # # ...take only contours whose area is larger
        # return [c for c in square_contours
        #     if cv2.contourArea(c) > thresh]
        #endregion

    # # Returns a numpy array of the ideal character cell contours.
    # def ideal_cell_contours(self) -> np.ndarray:
    #     # generate ideal contours
    #     spacer_lines = 0
    #     self._ideal_cell_contours = np.zeros((GRID_NUM_COLS*GRID_NUM_ROWS,4,2), np.uint16)
    #     for y in range(GRID_NUM_ROWS):
    #         # The official webpage has an additional row of pixels between every two
    #         # rows as a byproduct of CSS centering. This is how we mimic it:
    #         if not y%2:
    #             spacer_lines += 1

    #         for x in range(GRID_NUM_COLS):
    #             self._ideal_cell_contours[GRID_NUM_COLS*y+x] = [
    #                 [
    #                     GRID_PADDING + x*(GRID_MAX_CELL_SIZE + GRID_GAP),
    #                     GRID_PADDING + y*(GRID_MAX_CELL_SIZE + GRID_GAP) + spacer_lines
    #                 ],
    #                 [
    #                     GRID_PADDING + x*(GRID_MAX_CELL_SIZE + GRID_GAP) + GRID_MAX_CELL_SIZE - 1,
    #                     GRID_PADDING + y*(GRID_MAX_CELL_SIZE + GRID_GAP) + spacer_lines
    #                 ],
    #                 [
    #                     GRID_PADDING + x*(GRID_MAX_CELL_SIZE + GRID_GAP) + GRID_MAX_CELL_SIZE - 1,
    #                     GRID_PADDING + y*(GRID_MAX_CELL_SIZE + GRID_GAP) + spacer_lines + GRID_MAX_CELL_SIZE - 1
    #                 ],
    #                 [
    #                     GRID_PADDING + x*(GRID_MAX_CELL_SIZE + GRID_GAP),
    #                     GRID_PADDING + y*(GRID_MAX_CELL_SIZE + GRID_GAP) + spacer_lines + GRID_MAX_CELL_SIZE - 1
    #                 ]]
    #     return self._ideal_cell_contours


    # def intersectConvex(self):
    # # generate masks
    #     _, game_cell_mask = cv2.threshold(self.grayscale_mat, BG_DARK>>16, 255, cv2.THRESH_BINARY)
    #     cv2.imwrite('cell_mask.png', game_cell_mask)
    #     _, game_char_mask = cv2.threshold(self.grayscale_mat, 200, 255, cv2.THRESH_BINARY)
    #     cv2.imwrite('char_mask.png', game_char_mask)
        
    # # find contours
    #     self.cell_contours, _ = cv2.findContours(game_cell_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    #     cv2.imwrite('cell_contours.png', cv2.drawContours(self.image.copy(), self.cell_contours, -1, (0,0,255)))
    #     self.char_contours, _ = cv2.findContours(game_char_mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    #     cv2.imwrite('char_contours.png', cv2.drawContours(self.image.copy(), self.char_contours, -1, (0,0,255)))

    # # create line contours
    #     cell_contour = np.squeeze(self.cell_contours[0])
    #     char_contour = np.squeeze(self.char_contours[0])
    #     char_contour_convex = cv2.convexHull(char_contour)
    #     x, y, w, h = cv2.boundingRect(char_contour_convex)

    #     hoff = int(h*0.5)
    #     hboxline = np.array([
    #         [x,     y+hoff-1],
    #         [x+w,   y+hoff-1],
    #         [x+w,   y+hoff+1],
    #         [x,     y+hoff+1]])
    #     _, hx = cv2.intersectConvexConvex(char_contour, hboxline)
    #     hx = np.squeeze(hx.astype(int))

    #     voff = int(w*0.5)
    #     vboxline = np.array([
    #         [x+voff-1,    y],
    #         [x+voff-1,    y+h],
    #         [x+voff+1,    y+h],
    #         [x+voff+1,    y]])
    #     _, vx = cv2.intersectConvexConvex(char_contour_convex, vboxline)
    #     vx = np.squeeze(vx.astype(int))
        
    #     cv2.drawContours(self.image, [char_contour_convex], -1, (255,0,0))
    #     cv2.drawContours(self.image, [cell_contour, hx, vx], -1, (0,0,255))
    #     cv2.imwrite('intersections.png', self.image)
    #endregion

    def _generate_comparison_masks(self) -> None:
        assert len(self.cell_contours) > 0, 'This function must be called after the cell contours have been generated.'
        _, _, target_size, _ = cv2.boundingRect(self.cell_contours[0])
        
        # Preferable interpolation methods are cv.INTER_AREA for shrinking and cv.INTER_CUBIC (slow)
        # & cv.INTER_LINEAR for zooming. By default, the interpolation method cv.INTER_LINEAR is used
        # for all resizing purposes. [https://docs.opencv.org/4.x/da/d6e/tutorial_py_geometric_transformations.html]
        interp_mode = cv2.INTER_AREA if target_size < 155 else cv2 .INTER_LINEAR

        prepared_masks = []
        for char in self._alphabet:
            mask = cv2.imread(f'lib/character_masks/{char}.png', cv2.IMREAD_UNCHANGED)
            mask = cv2.resize(mask, (target_size, target_size), interpolation=interp_mode)
            prepared_masks.append(mask)

        self.char_compare_masks = prepared_masks
    
    def _generate_data(self) -> None:
        self.grayscale = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)

        # Cell data
        _, cells_mask = cv2.threshold(self.grayscale, 18, 255, cv2.THRESH_BINARY)
        self.cell_contours, _ = cv2.findContours(cells_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Character data
        self._generate_comparison_masks()
        self._generate_char_masks()

    def _generate_char_masks(self):
        _, chars_mask = cv2.threshold(self.grayscale, 200, 255, cv2.THRESH_BINARY)
        masks = []
        for c in self.cell_contours:
            x, y, w, h = cv2.boundingRect(c)
            _, mask = cv2.threshold(chars_mask[y:y+h, x:x+w], 200, 255, cv2.THRESH_BINARY)
            masks.append(mask)
        masks.reverse()
        self.char_masks = masks

    def _max_union(self):

        def hull_area(points):
            return cv2.contourArea(cv2.convexHull(points))

        guesses = []
        running_guess = ''
        for i, cmask in enumerate(self.char_masks):
            __max_union_area = 0
            max_index = 0
            # detect_e = []
            # detect_q = []
            for j, compmask in enumerate(self.char_compare_masks):
                union_area = cv2.countNonZero(cv2.bitwise_and(cmask, compmask))

                if union_area > __max_union_area:
                    __max_union_area = union_area
                    max_index = j
                    max_compmask = compmask
                    # if j == self._alphabet.index('e'):
                    #     detect_e.append(j)
                    # elif j == self._alphabet.index('q'):
                    #     detect_q.append(j)

            # currently this makes the following mistakes:
            #   L -> E
            #   O -> Q
            char = self._alphabet[max_index]
            if char == 'e':
                cmask_area = cv2.countNonZero(cmask)
                compmask_area = cv2.countNonZero(max_compmask)
                print(f'cmask: {cmask_area}\ncompmask: {compmask_area}\nunion: {__max_union_area}')
                # cmask_hull_area = hull_area(cv2.findContours(cmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE))
                # compmask_hull_area = hull_area(self.char_compare_masks[maxindex])
                # print(f'"L":\t\tcmask_hull_area = {cmask_hull_area}\n'
                #     f'    \t\tcompmask_hull_area = {compmask_hull_area}')

            elif char == 'q':
                pass

            running_guess += char

            if len(running_guess) == 5:
                guesses.append(running_guess)
                running_guess = ''
        return guesses




fd = open('wordle-game-1.png', 'rb')
image_bytes = fd.read()
fd.close()

imgproc = WordleImageProcessor(image_bytes)
beg = time.perf_counter()
guesses = imgproc._max_union()
end = time.perf_counter()
print(f'[{end-beg}s]: {guesses}')


# # generate each character mask
# fd = open('characters.png', 'rb')
# image_bytes = fd.read()
# fd.close()
# img = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
# gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
# _, mask = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY)
# contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
# for c, char in zip(contours, 'zyxwvutsrqponmlkjihgfedcba'):
#     x, y, w, h = cv2.boundingRect(c)
#     offset = int(w * 0.2)
#     char_mask = mask[y:y+h, x:x+w]
#     char_mask[:5,:] = 0
#     char_mask[h-5:,:] = 0
#     char_mask[:,:5] = 0
#     char_mask[:,w-5:] = 0
#     cv2.imwrite(f'lib/character_masks/{char}.png', char_mask)
