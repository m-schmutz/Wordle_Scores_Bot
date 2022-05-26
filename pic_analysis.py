import cv2
from cv2 import waitKey as wk
from cv2 import waitKey

blue = (0, 0, 255)
# img2_grey = cv2.cvtColor(img_black, cv2.COLOR_BGR2GRAY)
# cv2.imshow('img2_grey', img2_grey)
# cv2.waitKey(0)

# mask = cv2.inRange(img2_grey, 15, 25)

# test = cv2.bitwise_or(mask, img2_grey)

# cv2.imshow('test', test)
# cv2.waitKey(0)

img_white = cv2.imread('./test_images/wordle.jpg')
def get_threshold(img):
    img_grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    mask = cv2.inRange(img_grey, 15, 25)
    masked = cv2.bitwise_or(mask, img_grey)

    return masked

cv2.imshow('the original image', img_white)
img_black = cv2.imread('./test_images/wordle.png')
cv2.imshow('original white image', img_black)
wk(0)

img_grey = cv2.cvtColor(img_white, cv2.COLOR_BGR2GRAY)
cv2.imshow('img_grey', img_grey)
cv2,waitKey(0)
masked = get_threshold(img_black)

retval, thresholded = cv2.threshold(img_grey, 200, 255, cv2.THRESH_BINARY_INV)

cv2.imshow('threshold', thresholded)
cv2,waitKey(0)
cv2.destroyAllWindows()