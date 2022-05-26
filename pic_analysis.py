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


cv2.destroyAllWindows()