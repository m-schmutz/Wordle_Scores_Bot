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
    ltr = pytesseract.image_to_string(mask_rgb, lang="eng", config = f"--psm 10").strip()
    # might be useful in the future. Stackoverflow: https://stackoverflow.com/questions/20831612/getting-the-bounding-box-of-the-recognized-words-using-python-tesseract#54059166
    # data = pytesseract.image_to_boxes(mask_rgb, lang='eng', config = f'--psm 10 --oem 1 -c tessedit_char_blacklist=$')
    # print(data)

    #return ltr after it has been sanitized
    return check_ltr(ltr)



#takes in 
def get_subimages(img):
    img_grey    = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    mask        = cv2.inRange(img_grey, 15, 25)
    masked      = cv2.bitwise_or(mask, img_grey)
    _, thresh   = cv2.threshold(masked, 200, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    _,_,width,_ = cv2.boundingRect(contours[0]) # used literally just to calculate colorCheckOffset outside of loop
    colorCheckOffset = int(width * 0.2)         # the number of pixels to shift inward when checking cell's background color
    subimages = []

    for c in contours:
        x,y,w,_ = cv2.boundingRect(c)
        if thresh[y + colorCheckOffset, x + colorCheckOffset]:
            subimages = [img[y:y+w, x:x+w]] + subimages

    return subimages


# get each letter from subimages and create a list of the words as strings
def get_guesses(subimages):
    guesses = []
    for i in range(len(subimages) // WORD_LENGTH):
        guess = ""
        for j in range(WORD_LENGTH):
            guess += get_ltr(subimages[WORD_LENGTH*i + j])
        guesses.append(guess)
    return guesses
    # return [ "".join([ get_ltr(subimages[WORD_LENGTH * i + j]) for j in range(WORD_LENGTH) ]) for i in range(len(subimages) // WORD_LENGTH) ]



inputImage  = cv2.imread('./test_images/wordle6.png')
guesses     = get_guesses(get_subimages(inputImage))
print(guesses)

# cv2.waitKey(0)
# cv2.destroyAllWindows()