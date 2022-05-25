#! ./env/bin/python3
from xml.dom import HierarchyRequestErr
import cv2

blue = (0, 0, 255)

img = cv2.imread('./test_images/wordle.jpg')

imgcpy = img.copy()

grey_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

retval, thresh = cv2.threshold(grey_img, 50, 255, cv2.THRESH_BINARY)

cv2.imwrite('./thresh1.png', thresh)

img_contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

cv2.drawContours(imgcpy, img_contours, -1, blue, 5)

cv2.imwrite('./final1.png', imgcpy)