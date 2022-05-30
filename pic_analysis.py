#!./env/bin/python3
import cv2
import pytesseract

_PSM_SINGLE_LINE    = 7
_PSM_SINGLE_WORD    = 8
_PSM_SING_CHAR      = 10
_PSM_RAW_LINE       = 13
### Tesseract Manual [https://github.com/tesseract-ocr/tesseract/blob/main/doc/tesseract.1.asc] ###

TESS_CONFIG         = f"--psm {_PSM_SINGLE_LINE} --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ"
CELL_CHECK_FACTOR   = 0.2


def get_image_slice_data(cells_mask):

    # Get the contours of each cell
    cell_contours, _ = cv2.findContours(cells_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Get the cell height
    height = cv2.boundingRect(cell_contours[0])[3]

    # Get y-coordinate of each contour
    y_coords = []
    cellCheckOffset = int(height * CELL_CHECK_FACTOR)
    for c in cell_contours:
        x,y,_,_ = cv2.boundingRect(c)
        if (cells_mask[y + cellCheckOffset, x + cellCheckOffset]):
            y_coords.append(y)

    # Get every 5th coordinate (sorted, because then we know the indecies of each word and WORD_LENGTH)
    # The value grabbed may be a few pixels off, but this is negligible
    y_coords.sort()
    return y_coords[::5], height


def words_from_image(img):

    words = []

    # Convert image to grayscale so we can use cv2.threshold() & cv2.findContours()
    img_grayscale = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Get inverted binary mask of the characters
    # Pixels in range [200, 255] set to 0 (black), otherwise 1 (white)
    _, letters_mask = cv2.threshold(img_grayscale, 200, 255, cv2.THRESH_BINARY_INV)
    # cv2.imwrite('letters_mask.png', letters_mask)

    # Get binary mask of the character cells
    # Pixels in range [50, 255] set to 1 (white), otherwise 0 (black)
    _, cells_mask = cv2.threshold(img_grayscale, 50, 255, cv2.THRESH_BINARY)
    # cv2.imwrite('cells_mask.png', cells_mask)

    # Get information about how to slice the image (by word)
    slice_coords, slice_height = get_image_slice_data(cells_mask)

    # Generate a list of the words produced by pytesseract
    for y in slice_coords:
        slice = letters_mask[ y:y+slice_height, : ]
        word = pytesseract.image_to_string(slice, lang="eng", config=TESS_CONFIG).split()
        words.append(word)

    return words


# currently, pytesseract.image_to_string yields correct results most of the time.
# it may be beneficial to read by character rather than by word...
# NOTE: DOES NOT WORK ON IMAGES WITH WHITE BACKGROUNDS YET
# current misreads:
#   psm 7
#   - reading HONED as HONEOD   (wordle_dark_1.png)
#   psm 13
#   - reading BONEY as BOONEY   (wordle_dark_1.png)
#   - reading GUARD as GUAROD   (wordle_dark_2.png)
def main():
    image = cv2.imread("./test_images/wordle_dark_1.png")
    words = words_from_image(image)

    for word in words:
        print(word)

main()