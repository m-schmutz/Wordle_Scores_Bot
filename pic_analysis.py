#!./env/bin/python3
import cv2
import pytesseract
ryans-edits

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
=======
import numpy as np
from PIL import Image
import re
####################################################################
# number of characters in a row
ROW_LENGTH = 5
####################################################################
# These are ranges for the different colored squares.
# Ranges need to be expanded to allow for different shades
YELLOW_RANGE = (np.array([58, 158, 180]), np.array([60, 160, 182]))

GREY_RANGE = (np.array([59, 57, 57]), np.array([61, 59, 59]))

GREEN_RANGE = (np.array([77, 140, 82]), np.array([79, 142, 84]))

WHITE_RANGE = (np.array([200, 200, 200]), np.array([256, 256, 256]))
####################################################################
# characters that need to be substituted
# oh boy this image to text api is incredible
subs = {'l': 'I', 
        '0': 'O', 
        '|': 'I'}
####################################################################
# regular expression for detecting when two characters are the same
# and in the alphabet
TWINS = r'^([A-Z])\1$'
res = re.search
####################################################################
####################################################################
# functions are still old ones
# new ones are in branch ryans-edits


#checks output of pytesseract
def check_ltr(ltr):
    #try to substitute letter with known substitutions in the dict()
    try:
        #if letter is a key in dictionary, replace ltr with its mapping
        ltr = subs[ltr]
    #otherwise ignore step
    except:
        pass
    #prints ltr if needed
    #print(f'ltr.upper(): {ltr.upper()}')
    #check if ltr is two of the same letter
    if res(TWINS, ltr.upper()):
        #if it is two of the same letter, keep only one
        ltr = ltr[0]
    #return uppercase letter
    return ltr.upper()

#takes in subimage and returns ltr contained in subimage
def get_ltr(si):
    #create upper and lower bound ar##########
# GREEN  #  
# R: 83  #
# G: 141 #
# B: 78  #
##########rays
    #that represent range of white-ish pixels
    lower_bound, upper_bound = WHITE_RANGE
    #mask is the image that grabs only pixels that are white
    mask = cv2.inRange(si, lower_bound, upper_bound)
   
    #inverse image so that letter is black on white background
    mask = cv2.bitwise_not(mask)
    #convert to RGB so that pytesseract can read it
    mask_rgb = cv2.cvtColor(mask, cv2.COLOR_GRAY2RGB)
    #get output from pytesseract
    ltr = pytesseract.image_to_string(mask_rgb, lang='eng', config = f'--psm 10 --oem 1 -c tessedit_char_blacklist=$').strip()
    # might be useful in the future. Stackoverflow: https://stackoverflow.com/questions/20831612/getting-the-bounding-box-of-the-recognized-words-using-python-tesseract#54059166
    # data = pytesseract.image_to_boxes(mask_rgb, lang='eng', config = f'--psm 10 --oem 1 -c tessedit_char_blacklist=$')
    # print(data)

    #return ltr after it has been sanitized
    return check_ltr(ltr)
    
#takes in 
def get_subimages(img):
    # cv2.imshow('passed img', img)
    img_grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    mask = cv2.inRange(img_grey, 15, 25)
    # cv2.imshow('mask', mask)
    # cv2.imshow('img_grey', img_grey)

    masked = cv2.bitwise_or(mask, img_grey)
    # cv2.imshow('masked', masked)
    # cv2.waitKey(0)
    # cv2.imshow('masked', masked)
    retval, thresh = cv2.threshold(masked, 200, 255, cv2.THRESH_BINARY_INV)
    # cv2.imshow('thresh', thresh)
    # cv2.waitKey(0)
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # cv2.imshow('thresh', thresh)
    subimages = []
    for contour in contours:
        x,y,w,h = cv2.boundingRect(contour)
        subimages = [img[y:y+h, x:x+w]] + subimages
    return subimages

def get_guesses(subimages):
    rows = len(subimages) // 5
    guesses = []
    for i in range(rows):
        guess = ''
        start_ltr = i * ROW_LENGTH
        end_ltr = start_ltr + ROW_LENGTH
        for j in range(start_ltr, end_ltr):
            ltr = get_ltr(subimages[j])
            guess = guess + ltr
        if (guess != ''):
            guesses.append(guess)
    return guesses

def get_color(si):
    p = np.array([[si[0][0]]])
    lower_bound, upper_bound = GREEN_RANGE
    grnp = cv2.inRange(p, lower_bound, upper_bound)[0][0]
    if grnp:
        return 'green'
    lower_bound, upper_bound = YELLOW_RANGE
    yp = cv2.inRange(p, lower_bound, upper_bound)[0][0]
    if yp:
        return 'yellow'
    lower_bound, upper_bound = GREY_RANGE
    gryp = cv2.inRange(p, lower_bound, upper_bound)
    if gryp:
        return 'grey'

    
check_ltr('u')


# img_white = cv2.imread('./test_images/wordle5.png')


# subimages = get_subimages(img_white)

# si = subimages[0]

# print(get_color(si))

# # guesses = get_guesses(subimages)
# # print(guesses)

# cv2.waitKey(0)
# cv2.destroyAllWindows()
main
