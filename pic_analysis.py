#! ./env/bin/python3

import cv2
from cv2 import waitKey as wk

# img2_grey = cv2.cvtColor(img_black, cv2.COLOR_BGR2GRAY)
# cv2.imshow('img2_grey', img2_grey)
# cv2.waitKey(0)

# mask = cv2.inRange(img2_grey, 15, 25)

# test = cv2.bitwise_or(mask, img2_grey)

# cv2.imshow('test', test)
# cv2.waitKey(0)

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























# hsv = cv2.cvtColor(img_white, cv2.COLOR_BGR2HSV)
# cv2.imshow('HSV Image', hsv)
# wk(0)

# hue, saturation, value = cv2.split(hsv)
# cv2.imshow('Saturation Image', saturation)

# retval, thresholded = cv2.threshold(saturation, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
# cv2.imshow('Thresholded Image',thresholded)
# cv2.waitKey(0)

# medianFiltered = cv2.medianBlur(thresholded,5)
# cv2.imshow('Median Filtered Image',medianFiltered)
# cv2.waitKey(0) 

# cnts, hierarchy = cv2.findContours(medianFiltered, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)