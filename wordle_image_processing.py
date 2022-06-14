import cv2
import pytesseract
import constants as const
from multiprocessing import Pool, cpu_count

_DEBUG_GEN_IMGS = False
_DEBUG_PRINT    = False

#region INTERNAL FUNCTIONS =================================================================
### __try_blurs:
############################################################################################
# Attempts to extract a character from an image slice using a variety of different blur
# factors, BLUR_FACTORS. If it returns None, no character could be read by Tesseract.
def __try_blurs(img):

    for blur in const.BLUR_FACTORS:
        _tess_source = cv2.blur( img, blur )
        _tess_output = pytesseract.image_to_string( _tess_source, lang="eng", config=const.TESS_CONFIG )
        _char = _tess_output.strip()
        if _char != "":
            return _char

    return None

### __process_words:
############################################################################################
# Generates a list of words using positional image data and the image img_chars containing
# each word/guess.
def __process_words(img_chars, cells_mask, cells, cell_width):

    offset = int(cell_width * const.CELL_CHECK_FACTOR) # The x/y-offset, in pixels

    # Create a sorted list of each character image.
    # It's size will always be a multiple of WORD_LEN.
    # - We cannot gurantee that each character cell was produced in order from
    #   left-to-right, so we will sort the cells by x/y-coordinates from top-to-bottom
    #   and left-to-right, with priority to the former. This way we can ensure every
    #   sequential subset of length WORD_LEN, starting at 0, contains the correct
    #   characters. We then sort each subset from left-right, to produce the correct
    #   word/guess made by the player.
    cell_imgs = []
    num_rows = len(cells) // const.WORD_LEN
    cells.sort( key=lambda c: (c[1], c[0]) )
    for i in range(num_rows):
        _beg        = i * const.WORD_LEN
        _row_cells  = cells[_beg : _beg + const.WORD_LEN]

        # If any cell mask in the current row is 0, we know there are no more guesses
        # and can stop obtaining images to read
        _sample_cell = _row_cells[0]
        _x_offset    = _sample_cell[0] + offset
        _y_offset    = _sample_cell[1] + offset
        if not cells_mask[_y_offset, _x_offset]:
            break
        
        # Sort the row
        _row_cells.sort( key=lambda c: c[0] )
        for cell in _row_cells:
            _x     = cell[0]                    # x-coord of the cell's top-left point
            _y     = cell[1]                    # y-coord of the cell's top-left point
            _x_beg = _x + offset                # north slice bound
            _y_end = _y + cell_width - offset   # east slice bound
            _x_end = _x + cell_width - offset   # south slice bound
            _y_beg = _y + offset                # west slice bound

            # Append image of the given character to list
            _img_char = img_chars[ _y_beg:_y_end, _x_beg:_x_end ]
            cell_imgs.append(_img_char)

    # Create multiple processes to process character images quickly
    # using half as many cores seems to be the quickest. perhaps tesseract reserves a core itself?
    raw_num_cores = cpu_count()
    num_cores     = raw_num_cores // 2
    if _DEBUG_PRINT: print(f"Detected {raw_num_cores} cores, using {num_cores}.")
    chars         = Pool(num_cores).map(__try_blurs, cell_imgs)

    # Reconstruct the words from the list of characters read by Tesseract
    words    = []
    num_rows = len(chars) // const.WORD_LEN
    for i in range(num_rows):
        _beg  = i * const.WORD_LEN
        _word = "".join(chars[_beg : _beg + const.WORD_LEN])
        words.append(_word)
    if _DEBUG_PRINT: print("word list =", words)

    return words

### __is_uniform:
############################################################################################
# Returns True when all items in the array are list-equivalent
#   - helper for _valid_margin()
def __is_uniform(array):
    array = array.tolist()
    sample = array[0]

    for elem in array:
        if elem != sample:
            return False

    return True

### __validate_margin:
############################################################################################
# We test the outermost edges of the image to disallow the image submission
# to be processed. By demanding a more structured input, we alleviate the amount
# of processing necessary.
def __validate_margin(img):

    # Each edge/slice of the image (and no, i don't feel like getting rid of the redundant corner checks)
    height     = img.shape[0]
    width      = img.shape[1]
    img_north  = img[0, :]
    img_east   = img[:, width-1]
    img_south  = img[height-1, :]
    img_west   = img[:, 0]

    # Check each edge
    if not __is_uniform(img_north): return False
    if not __is_uniform(img_east):  return False
    if not __is_uniform(img_south): return False
    if not __is_uniform(img_west):  return False
    if _DEBUG_GEN_IMGS:
        cv2.imwrite("debug_images_dump/top_edge.png", img_north)
        cv2.imwrite("debug_images_dump/left_edge.png", img_east)
        cv2.imwrite("debug_images_dump/bottom_edge.png", img_south)
        cv2.imwrite("debug_images_dump/right_edge.png", img_west)

    return True

### _get_masks:
############################################################################################
# Generate a mask for both the character cells and the characters themselves.
def __gen_masks(img):

    # Convert image to grayscale so we can use cv2.threshold() & cv2.findContours()
    img_grayscale = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _sample_pixel = img[0, 0]
    light_theme   = all( val >= const.GRAYSCALE_MASK_THRESH for val in _sample_pixel )

    # Generate the cells and characters masks
    # Light Theme
    if light_theme:
        _, _cells_mask_inv      = cv2.threshold(img_grayscale, const.CELLS_MASK_THRESH_LIGHT, const.THRESH_MAX, cv2.THRESH_BINARY)
        chars_mask = cells_mask = cv2.bitwise_not(_cells_mask_inv)
    # Dark Theme
    else:
        _, cells_mask = cv2.threshold(img_grayscale, const.CELLS_MASK_THRESH_DARK, const.THRESH_MAX, cv2.THRESH_BINARY)
        _, chars_mask = cv2.threshold(img_grayscale, const.CHARS_MASK_THRESH_DARK, const.THRESH_MAX, cv2.THRESH_BINARY_INV)

    # Make sure the image was cropped correctly
    if not __validate_margin(cells_mask):
        quit("Error: Image needs to have a margin of space around the board!")

    if _DEBUG_GEN_IMGS:
        cv2.imwrite("debug_images_dump/cells_mask.png", cells_mask)
        cv2.imwrite("debug_images_dump/chars_mask.png", chars_mask)
        cv2.imwrite("debug_images_dump/img_grayscale.png", img_grayscale)

    return chars_mask, cells_mask
#endregion =================================================================================



#region Functions for external use: ========================================================
### get_guesses:
############################################################################################
# Given a cropped screenshot of a Worlde game, produces a list of the player's guesses.
def get_guesses(img):

    # Generate a mask of the cells and characters
    chars_mask, cells_mask = __gen_masks(img)

    # Next, we will extract information from the contours produced by OpenCV.
    cell_contours, _   = cv2.findContours(cells_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    _sample_cell        = cell_contours[0]
    _, _, cell_width, _ = cv2.boundingRect(_sample_cell)

    # Get the x/y-coordinate of each cell and their shared width
    cells = []
    for contour in cell_contours:
        _x, _y, _, _ = cv2.boundingRect(contour)
        cells.append((_x, _y))

    if _DEBUG_GEN_IMGS:
        _img_cell_contours = cv2.drawContours(img.copy(), cell_contours, -1, (0,0,255))
        cv2.imwrite('debug_images_dump/img_contours.png', _img_cell_contours)

        img_crosshairs = img.copy()
        radius = cell_width // 20  # arbitrary value
        for cell in cells:
            _x = cell[0]
            _y = cell[1]
            img_crosshairs[ _y - radius : _y + radius, _x ] = (0,0,255)
            img_crosshairs[ _y, _x - radius : _x + radius ] = (0,0,255)
        cv2.imwrite("debug_images_dump/img_crosshairs.png", img_crosshairs)

    # Finally, we can construct a list of the words using Tesseract
    return __process_words(chars_mask, cells_mask, cells, cell_width)
#endregion =================================================================================
