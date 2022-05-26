#!./env/bin/python3
import cv2
import pytesseract
import numpy as np


blue = (0, 0, 255)
ROW_LENGTH = 5

def invert_ltr(si):
    lower_bound = np.array([200, 200, 200])
    upper_bound = np.array([256, 256, 256])

    mask = cv2.inRange(si, lower_bound, upper_bound)
    cv2.imwrite('./mask.png', mask)
    
    


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

def get_words(subimages):
    rows = len(subimages) // 5
    guesses = [''] * rows

    si = subimages[0]

    cv2.imwrite('./si.png', si)

    si_rgb = cv2.cvtColor(subimages[0], cv2.COLOR_BGR2RGB)

    cv2.imwrite('./si_rgb.png', si_rgb)

    invert_ltr(si_rgb)

    # print(pytesseract.image_to_string(si_rgb))



    # for i in range(rows):
    #     j = i * ROW_LENGTH
    #     guesses[i] = ''.join([si for si in subimages[j:j + ROW_LENGTH]])
    # return guesses
        
        
        


img_white = cv2.imread('./test_images/wordle.jpg')

# img_black = cv2.imread('./test_images/wordle.png')


subimages = get_subimages(img_white)

# for i, si in enumerate(subimages):
#     cv2.imwrite(f'./cropped/si{i}.png', si)

#subimages = ['0','1', '2', '3', '4', '5', '6', '7', '8', '9']


get_words(subimages)

#print(guesses)

