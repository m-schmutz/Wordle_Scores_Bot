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
CONFIG = f'--oem {OEM_DEFAULT} --psm {PSM_SINGLE_BLOCK} -c tessedit_char_whitelist={ALPHABET.upper()}'

COLS = 5    # i.e. number of characters per word
SQUARE_THRESH = 2   # the highest permissible difference between the width and height of a cell contour
SQUARE_NPSIZE = 8  # 4 pairs of x/y-coords


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
    def __init__(self, image: bytes) -> None:
        self.image = cv2.imdecode(np.frombuffer(image, np.uint8), cv2.IMREAD_COLOR)
        self.grayscale = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        self.darkTheme = np.median(self.grayscale[:1,:]) < 200

        self.cell_mask = self._genCellMask()
        self.cell_contours = self._genCellContours()
        self.chars_mask = self._genCharMask()

    def _genCellMask(self, save: bool = False) -> cv2.Mat:
        if self.darkTheme:
            thresh = 30
            mode = cv2.THRESH_BINARY
        else:
            thresh = 200
            mode = cv2.THRESH_BINARY_INV

        _, mask = cv2.threshold(self.grayscale, thresh, 255, mode)

        if save:
            cv2.imwrite('tests/cell_mask.png', mask)

        return mask

    def _genCellContours(self, save: bool = False) -> 'list[np.ndarray]':
        contours, _ = cv2.findContours(self.cell_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Remove all axis of length one since they are useless. Additionally, reverse
        # the list since cv2.findContours works from SE to NW and we want our contours
        # organized from NW to SE (i.e. guess order).
        contours = np.squeeze(contours)[::-1]

        if save:
            cv2.imwrite('tests/cell_contours.png', cv2.drawContours(self.image, contours, -1, (0,0,255)))

        return contours

    def _genCharMask(self, save: bool = False) -> cv2.Mat:
        _, mask = cv2.threshold(self.grayscale, 200, 255, cv2.THRESH_BINARY_INV)

        # squeeze letters horizontally
        cols = list()
        for c in self.cell_contours[:COLS]:
            x,_,w,_ = cv2.boundingRect(c)
            off = w//4
            cols.append(mask[:, x+off:x+w-off])
        mask = cv2.hconcat(cols)

        # crop vertically
        ys = list(y for contour in self.cell_contours
            for (_, y) in contour)
        mask = mask[min(ys):max(ys), :]

        # potentially fill empty horizontal strips
        if not self.darkTheme:
            for i in range(mask.shape[0]):
                if all(mask[i,:] == 0):
                    mask[i,:] = 255

        if save:
            cv2.imwrite('tests/chars_mask.png', mask)

        return mask

    def getWords(self) -> 'list[str]':
        text = image_to_string(self.chars_mask, lang="eng", config=CONFIG)
        return text.strip().split('\n')


@timer
def main():
    fd = open(f'wordle-game-light5.png', 'rb')
    image_bytes = fd.read()
    fd.close()

    wip = WordleImageProcessor(image_bytes)
    words = wip.getWords()
    print(words)

if __name__ == '__main__':
    main()
