#!./env/bin/python3

from re import sub
import cv2
from cv2 import boundingRect

blue = (0, 0, 255)
# img2_grey = cv2.cvtColor(img_black, cv2.COLOR_BGR2GRAY)
# cv2.imshow('img2_grey', img2_grey)
# cv2.waitKey(0)

# mask = cv2.inRange(img2_grey, 15, 25)

# test = cv2.bitwise_or(mask, img2_grey)

# cv2.imshow('test', test)
# cv2.waitKey(0)

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

img_white = cv2.imread('./test_images/wordle.jpg')
cv2.imwrite('./white.png', img_white)

img_black = cv2.imread('./test_images/wordle.png')


subimages = get_subimages(img_black)

for i, si in enumerate(subimages):
    cv2.imwrite(f'./cropped/si{i}.png', si)



