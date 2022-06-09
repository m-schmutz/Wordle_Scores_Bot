WORD_LEN            = 5     # Worlde word length
NUM_MAX_WORDS       = 6     # Worlde maximum number of guesses
CELL_CHECK_FACTOR   = 0.2   # This helps Tesseract produce more consitent and correct characters
BLUR_FACTORS        = [ (3,3), (5,5), (3,5), (5,3), (1,5), (5,1) ]  # idk seemed to resolve all misreads i saw

#region Tesseract
# Manual [https://github.com/tesseract-ocr/tesseract/blob/main/doc/tesseract.1.asc]
_OEM_ORIG           = 0     # "Original Tesseract only."
_OEM_NEURAL_LSTM    = 1     # "Neural nets LSTM only."
_OEM_TESS_LSTM      = 2     # "Tesseract + LSTM."
_OEM_DEFAULT        = 3     # "Default, based on what is available."

_PSM_OSD            = 0     # "Orientation and script detection (OSD) only."
_PSM_AUTO_OSD       = 1     # "Automatic page segmentation with OSD."
_PSM_AUTO           = 2     # "Automatic page segmentation, but no OSD, or OCR. (not implemented)"
_PSM_DEFAULT        = 3     # "Fully automatic page segmentation, but no OSD. (Default)"
_PSM_SINGLE_COL     = 4     # "Assume a single column of text of variable sizes."
_PSM_SINGLE_VBLOCK  = 5     # "Assume a single uniform block of vertically aligned text."
_PSM_SINGLE_BLOCK   = 6     # "Assume a single uniform block of text."
_PSM_SINGLE_LINE    = 7     # "Treat the image as a single text line."
_PSM_SINGLE_WORD    = 8     # "Treat the image as a single word."
_PSM_CIRCLE         = 9     # "Treat the image as a single word in a circle."
_PSM_SINGLE_CHAR    = 10    # "Treat the image as a single character."
_PSM_SPARSE         = 11    # "Sparse text. Find as much text as possible in no particular order."
_PSM_SPARSE_OSD     = 12    # "Sparse text with OSD."
_PSM_RAW_LINE       = 13    # "Raw line. Treat the image as a single text line, bypassing hacks that are Tesseract-specific."

_TESS_WHITELIST     = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
TESS_CONFIG         = f"--psm {_PSM_SINGLE_CHAR} --oem {_OEM_DEFAULT} -c tessedit_char_whitelist={_TESS_WHITELIST}"
#endregion
