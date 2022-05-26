#! ./env/bin/python3

import cv2
from cv2 import waitKey as wk
from cv2 import waitKey

blue = (0, 0, 255)

img_white = cv2.imread('./test_images/wordle.jpg')

cv2.imshow('the original image', img_white)
wk(0)

img_grey = cv2.cvtColor(img_white, cv2.COLOR_BGR2GRAY)
cv2.imshow('img_grey', img_grey)
cv2,waitKey(0)

retval, thresholded = cv2.threshold(img_grey, 200, 255, cv2.THRESH_BINARY_INV)

cv2.imshow('threshold', thresholded)
cv2,waitKey(0)
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