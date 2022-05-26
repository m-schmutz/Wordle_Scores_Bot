#!./env/bin/python3
from tkinter.tix import ROW
from turtle import end_fill
import cv2
import pytesseract
import numpy as np
from PIL import Image

ROW_LENGTH = 5

#checks output of pytesseract
def check_ltr(ltr):
    #only consider the first letter given and strip() new lines
    ltr = ltr[0].strip()
    #tesseract thinks that 'I' is 'l', so reverse this
    # this is safe to do because Wordle only has letters as uppercase
    if ltr == 'l':
        ltr = 'I'
    if ltr == '0':
        ltr = 'O'
    #return uppercase letter
    return ltr.upper()

#takes in subimage and returns ltr contained in subimage
def get_ltr(si):
    #create upper and lower bound arrays
    #that represent range of white-ish pixels
    lower_bound = np.array([200, 200, 200])
    upper_bound = np.array([256, 256, 256])
    #mask is the image that grabs only pixels that are white
    mask = cv2.inRange(si, lower_bound, upper_bound)
    #inverse image so that letter is black on white background
    mask = cv2.bitwise_not(mask)
    #convert to RGB so that pytesseract can read it
    mask_rgb = cv2.cvtColor(mask, cv2.COLOR_GRAY2RGB)
    #get output from pytesseract
    ltr = pytesseract.image_to_string(mask_rgb, lang='eng', config = f'--psm 10 --oem 1 -c tessedit_char_blacklist=$')
    
    #might be useful in the future. Stackoverflow: https://stackoverflow.com/questions/20831612/getting-the-bounding-box-of-the-recognized-words-using-python-tesseract#54059166
    # data = pytesseract.image_to_boxes(mask_rgb, lang='eng', config = f'--psm 10 --oem 1 -c tessedit_char_blacklist=$')
    # print(data)

    #return ltr after it has been sanitized
    return check_ltr(ltr)
    
#takes in 
def get_subimages(img):
    img_grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    mask = cv2.inRange(img_grey, 15, 25)

    masked = cv2.bitwise_or(mask, img_grey)
    retval, thresh = cv2.threshold(masked, 200, 255, cv2.THRESH_BINARY_INV)
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
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


img_white = cv2.imread('./test_images/wordle6.png')

subimages = get_subimages(img_white)

guesses = get_guesses(subimages)
print(guesses)


