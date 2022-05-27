#!./env/bin/python3
from string import ascii_lowercase, ascii_uppercase
import cv2
import pytesseract
import numpy as np
from PIL import Image
import re

ROW_LENGTH = 5

YELLOW_RANGE = ()

GREY_RANGE = ()

WHITE_RANGE = (np.array([200, 200, 200]), np.array([256, 256, 256]))


subs = {'l': 'I', '0': 'O'}


TWINS = r'^(A-Z)\1$'
res = re.search
#checks output of pytesseract
def check_ltr(ltr):
    l_ltr = list(ltr)
    print(f'ltr: {ltr}')
    try:
        ltr = subs[ltr]
    except:
        pass
    
    if res(TWINS, ltr.upper()):
        ltr = ltr[0]

    #return uppercase letter
    return ltr.upper()

#takes in subimage and returns ltr contained in subimage
def get_ltr(si):
    #create upper and lower bound arrays
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
    retval, thresh = cv2.threshold(masked, 200, 255, cv2.THRESH_BINARY_INV)
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


img_white = cv2.imread('./test_images/wordle5.png')


subimages = get_subimages(img_white)

si = subimages[0]

# cv2.imshow('subimage', si)
# cv2.waitKey(0)
##########
# GREEN  #  
# R: 83  #
# G: 141 #
# B: 78  #
##########
print(str(ascii_uppercase))

# GREEN_RANGE = (np.array([200, 200, 200]), np.array([256, 256, 256]))

# lower_bound, upper_bound = GREEN_RANGE

# mask = cv2.inRange(si, )

guesses = get_guesses(subimages)
print(guesses)

cv2.waitKey(0)
cv2.destroyAllWindows()