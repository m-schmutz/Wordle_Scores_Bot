#! ./env/bin/python3

import cv2
from cv2 import CHAIN_APPROX_NONE

blue = (0, 0, 255)

img_white = cv2.imread('./test_images/wordle.jpg')

img_black = cv2.imread('./test_images/wordle.png')



t_lower = 255
t_upper = 255

canny_img = cv2.Canny(img_white, t_lower, t_upper, 7)

contours, _ = cv2.findContours(canny_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

drawn_contours = img_white.copy()
cv2.drawContours(drawn_contours, contours, -1, blue, 2)


cv2.imshow('canny', canny_img)
cv2.waitKey(0)

cv2.imshow('drawn_contours', drawn_contours)
cv2.waitKey(0)


cv2.destroyAllWindows()