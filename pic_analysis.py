#!./env/bin/python3
from string import ascii_lowercase, ascii_uppercase
import cv2
import pytesseract
import numpy as np
from PIL import Image
import re

WORD_LENGTH = 5
YELLOW_RANGE= ()
GREY_RANGE  = ()
WHITE_RANGE = (np.array([200, 200, 200]), np.array([256, 256, 256]))
TWINS       = r'^([A-Z])\1$'

res = re.search
subs = {
    'l': 'I',
    '0': 'O',
    '$': 'S',
    's': 'S',
    'v': 'V',
}



#checks output of pytesseract
def check_ltr(ltr):
    l_ltr = list(ltr)
    print(f'String recieved: {ltr}')
    try:
        ltr = subs[ltr]
    except:
        pass
    
    if res(TWINS, ltr.upper()):
        ltr = ltr[0]

    #return uppercase letter
    return ltr.upper()



#takes in subimage and returns ltr contained in subimage
# def get_ltr(si):
#     #create upper and lower bound arrays
#     #that represent range of white-ish pixels
#     lower_bound, upper_bound = WHITE_RANGE
#     #mask is the image that grabs only pixels that are white
#     mask = cv2.inRange(si, lower_bound, upper_bound)
#     #inverse image so that letter is black on white background
#     mask = cv2.bitwise_not(mask)
#     #convert to RGB so that pytesseract can read it
#     mask_rgb = cv2.cvtColor(mask, cv2.COLOR_GRAY2RGB)
#     #get output from pytesseract
#     ltr = pytesseract.image_to_string(mask_rgb, lang="eng", config = f"--psm 10").strip()
#     # might be useful in the future. Stackoverflow: https://stackoverflow.com/questions/20831612/getting-the-bounding-box-of-the-recognized-words-using-python-tesseract#54059166
#     # data = pytesseract.image_to_boxes(mask_rgb, lang='eng', config = f'--psm 10 --oem 1 -c tessedit_char_blacklist=$')
#     # print(data)

#     #return ltr after it has been sanitized
#     return check_ltr(ltr)



#takes in 
# def get_subimages(img):
#     img_grey    = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#     mask        = cv2.inRange(img_grey, 15, 25)
#     masked      = cv2.bitwise_or(mask, img_grey)
#     _, thresh   = cv2.threshold(masked, 200, 255, cv2.THRESH_BINARY_INV)
#     contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
#     _,_,width,_ = cv2.boundingRect(contours[0]) # used literally just to calculate colorCheckOffset outside of loop
#     colorCheckOffset = int(width * 0.2)         # the number of pixels to shift inward when checking cell's background color
#     subimages = []

#     for c in contours:
#         x,y,w,_ = cv2.boundingRect(c)
#         if thresh[y + colorCheckOffset, x + colorCheckOffset]:
#             subimages = [img[y:y+w, x:x+w]] + subimages

#     return subimages


# # get each letter from subimages and create a list of the words as strings
# def get_guesses(subimages):
#     guesses = []
#     for i in range(len(subimages) // WORD_LENGTH):
#         guess = ""
#         for j in range(WORD_LENGTH):
#             guess += get_ltr(subimages[WORD_LENGTH*i + j])
#         guesses.append(guess)
#     return guesses
#     # return [ "".join([ get_ltr(subimages[WORD_LENGTH * i + j]) for j in range(WORD_LENGTH) ]) for i in range(len(subimages) // WORD_LENGTH) ]


def get_img_slice_data(cell_mask, contours):

    # Get the height of any contour
    height = cv2.boundingRect(contours[0])[3]

    # Get y-coordinate of each contour
    # y_coords = [ cv2.boundingRect(c)[1] for c in contours ]
    y_coords = []
    cellCheckOffset = int(0.2 * height)
    for c in contours:
        x,y,_,_ = cv2.boundingRect(c)
        if (cell_mask[y + cellCheckOffset, x + cellCheckOffset]):
            y_coords.append(y)

    # Get every 5th coordinate (sorted, because then we know the indecies of each word and WORD_LENGTH)
    # The value grabbed may be a few pixels off, but this is negligible
    y_coords.sort()
    return y_coords[::5], height


def get_words_for_pytesseract(img):

    # Convert image to grayscale
    img_grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # cv2.imwrite("im_grey.png", img_grey)

    # Get binary mask of the character cells
    # Pixels in range [50, 255] set to 1 (white), otherwise 0 (black)
    cell_mask = cv2.inRange(img_grey, 50, 255)
    cv2.imwrite("cell_mask.png", cell_mask)

    # Get the contour of each cell
    cell_contours, _ = cv2.findContours(cell_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Get the y-coordinates of each image slice and their height
    slices_coords, slice_height = get_img_slice_data(cell_mask, cell_contours)

    # but i also need to get letter contours... so should i get all contours and use
    # the hierarchy to separate cells from letters?

    return



inputImage  = cv2.imread('./test_images/wordle3.png')
get_words_for_pytesseract(inputImage)
# subimages   = get_subimages(inputImage)
# guesses     = get_guesses(subimages)
# print(guesses)

# cv2.waitKey(0)
# cv2.destroyAllWindows()