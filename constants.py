# Wordle General
WORD_LEN                = 5     # Wordle word length
# NUM_MAX_GUESSES         = 6     # Wordle maximum number of guesses

# Wordle Image Processing
CELL_CHECK_FACTOR       = 0.2   # This helps Tesseract produce more consitent and correct characters
BLUR_FACTORS            = [ (3,3), (5,5), (3,5), (5,3), (1,5), (5,1) ]  # idk seemed to resolve all misreads i saw
THRESH_MAX              = 255
GRAYSCALE_MASK_THRESH   = 100
CELLS_MASK_THRESH_DARK  = 50
CHARS_MASK_THRESH_DARK  = 200
CELLS_MASK_THRESH_LIGHT = 200



# Tesseract OEM/PSM Configuration Numbers
#   - Manual [https://github.com/tesseract-ocr/tesseract/blob/main/doc/tesseract.1.asc]
__OEM_ORIG          = 0     # "Original Tesseract only."
__OEM_NEURAL_LSTM   = 1     # "Neural nets LSTM only."
__OEM_TESS_LSTM     = 2     # "Tesseract + LSTM."
__OEM_DEFAULT       = 3     # "Default, based on what is available."
__PSM_OSD           = 0     # "Orientation and script detection (OSD) only."
__PSM_AUTO_OSD      = 1     # "Automatic page segmentation with OSD."
__PSM_AUTO          = 2     # "Automatic page segmentation, but no OSD, or OCR. (not implemented)"
__PSM_DEFAULT       = 3     # "Fully automatic page segmentation, but no OSD. (Default)"
__PSM_SINGLE_COL    = 4     # "Assume a single column of text of variable sizes."
__PSM_SINGLE_VBLOCK = 5     # "Assume a single uniform block of vertically aligned text."
__PSM_SINGLE_BLOCK  = 6     # "Assume a single uniform block of text."
__PSM_SINGLE_LINE   = 7     # "Treat the image as a single text line."
__PSM_SINGLE_WORD   = 8     # "Treat the image as a single word."
__PSM_CIRCLE        = 9     # "Treat the image as a single word in a circle."
__PSM_SINGLE_CHAR   = 10    # "Treat the image as a single character."
__PSM_SPARSE        = 11    # "Sparse text. Find as much text as possible in no particular order."
__PSM_SPARSE_OSD    = 12    # "Sparse text with OSD."
__PSM_RAW_LINE      = 13    # "Raw line. Treat the image as a single text line, bypassing hacks that are Tesseract-specific."

TESS_WHITELIST  = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
TESS_CONFIG     = f"--psm {__PSM_SINGLE_CHAR} --oem {__OEM_DEFAULT} -c tessedit_char_whitelist={TESS_WHITELIST}"
