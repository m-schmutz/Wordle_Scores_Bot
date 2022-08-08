import numpy as np
import cv2
from pytesseract import image_to_string
import time
import ansi

OEM_ORIG            = 0     # "Original Tesseract only."
OEM_NEURAL_LSTM     = 1     # "Neural nets LSTM only."
OEM_TESS_LSTM       = 2     # "Tesseract + LSTM."
OEM_DEFAULT         = 3     # "Default, based on what is available."

PSM_OSD             = 0     # "Orientation and script detection (OSD) only."
PSM_AUTO_OSD        = 1     # "Automatic page segmentation with OSD."
PSM_AUTO            = 2     # "Automatic page segmentation, but no OSD, or OCR. (not implemented)"
PSM_DEFAULT         = 3     # "Fully automatic page segmentation, but no OSD. (Default)"
PSM_SINGLE_COL      = 4     # "Assume a single column of text of variable sizes."
PSM_SINGLE_VBLOCK   = 5     # "Assume a single uniform block of vertically aligned text."
PSM_SINGLE_BLOCK    = 6     # "Assume a single uniform block of text."
PSM_SINGLE_LINE     = 7     # "Treat the image as a single text line."
PSM_SINGLE_WORD     = 8     # "Treat the image as a single word."
PSM_CIRCLE          = 9     # "Treat the image as a single word in a circle."
PSM_SINGLE_CHAR     = 10    # "Treat the image as a single character."
PSM_SPARSE          = 11    # "Sparse text. Find as much text as possible in no particular order."
PSM_SPARSE_OSD      = 12    # "Sparse text with OSD."
PSM_RAW_LINE        = 13    # "Raw line. Treat the image as a single text line, bypassing hacks that are Tesseract-specific."

ALPHABET = 'abcdefghijklmnopqrstuvwxyz'
CONFIG = f'--oem {OEM_DEFAULT} --psm {PSM_SINGLE_LINE} -c tessedit_char_whitelist={ALPHABET.upper()}'

COLS = 5    # i.e. number of characters per word
SQUARE_THRESH = 2   # the highest permissible difference between the width and height of a cell contour
SQUARE_ARRSIZE = 8  # 4 pairs of x/y-coords



# decorator function for timing purposes
def timer(func):
    def _inner(*args, **kwargs):
        beg = time.perf_counter()
        ret = func(*args, **kwargs)
        end = time.perf_counter()
        print(ansi.magenta(f'[{end-beg:.06f}]: {func.__name__}'))
        return ret
    return _inner


class WordleImageProcessor:
    def __init__(self, image: bytes, *, area_margin: int = 50) -> None:
        self.image: cv2.Mat = cv2.imdecode(np.frombuffer(image, np.uint8), cv2.IMREAD_COLOR)
        self.grayscale: cv2.Mat = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)

        ######## TODO
        ######## Determine if light or dark theme is being used in order to apply correct thresholds
        _, self.cells_mask = cv2.threshold(self.grayscale, 50, 255, cv2.THRESH_BINARY) # ASSUMES DARK THEME
        ######## TODO
        ######## Programatically find the board and keep only cell contours
        self.cell_contours: list[np.ndarray] = self.genCellContours()
        
        ######## TODO
        ######## 
        self.chars_mask: cv2.Mat = self.genCharMask()

    @timer
    def genCharMask(self) -> cv2.Mat:
        cols = []
        _, mask = cv2.threshold(self.grayscale, 200, 255, cv2.THRESH_BINARY_INV) # ASSUMES DARK THEME
        for i in range(COLS):
            x,_,w,_ = cv2.boundingRect(self.cell_contours[i])
            off = w//4
            cols.insert(0, mask[:, x+off:x+w-off])
        mask = cv2.hconcat(cols)

        # cv2.imwrite('chars_mask.png', self.chars_mask)
        return mask

    @timer
    def genCellContours(self) -> 'list[np.ndarray]':
        filtered = list()
        contours, _ = cv2.findContours(self.cells_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for c in contours:
            # disregard any contours that are not a quadrilateral
            if c.size != SQUARE_ARRSIZE:
                continue

            # disregard any contour whose bounding box is not approximately a square
            x, y, w, h = cv2.boundingRect(c)
            if abs(w - h) > SQUARE_THRESH:
                continue
            
            if not self.cells_mask[y+h//2, x+w//2]:
                continue

            filtered.append(c)
        return np.squeeze(filtered)

    @timer
    def getWords(self):
        text = image_to_string(self.chars_mask, lang="eng", config=f'--psm {PSM_SINGLE_BLOCK} -c tessedit_char_whitelist={ALPHABET.upper()}').strip()
        return text.split('\n')


@timer
def main():
    fd = open('wordle-game-7.png', 'rb')
    image_bytes = fd.read()
    fd.close()
    imgproc = WordleImageProcessor(image_bytes)
    print(imgproc.getWords())

if __name__ == '__main__':
    main()
