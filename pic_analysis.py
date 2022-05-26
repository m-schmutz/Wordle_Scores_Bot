#! ./env/bin/python3

import cv2
from cv2 import waitKey as wk

def get_threshold(img):
    img_grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    mask = cv2.inRange(img_grey, 15, 25)
    masked = cv2.bitwise_or(mask, img_grey)
    
    return masked

img_black = cv2.imread('./test_images/wordle.png')
cv2.imshow('original white image', img_black)
wk(0)

masked = get_threshold(img_black)


cv2.destroyAllWindows()

