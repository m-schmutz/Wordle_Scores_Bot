# def get_image_slice_data(cells_mask):

#     # Get the contours of each cell
#     cell_contours, _ = cv2.findContours(cells_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

#     # Get the cell height
#     height = cv2.boundingRect(cell_contours[0])[3]

#     # Get y-coordinate of each contour
#     y_coords = []
#     cellCheckOffset = int(height * CELL_CHECK_FACTOR)
#     for c in cell_contours:
#         x,y,_,_ = cv2.boundingRect(c)
#         if (cells_mask[y + cellCheckOffset, x + cellCheckOffset]):
#             y_coords.append(y)

#     # Get every 5th coordinate (sorted, because then we know the indecies of each word and WORD_LENGTH)
#     # The value grabbed may be a few pixels off, but this is negligible
#     y_coords.sort()
#     return y_coords[::5], height




# Contours of cells are stored as a list FOUR pairs of x/y-coordinates
# starting at the top-left point, moving clockwise:
#
#    contour              index
#   A-------B       A: contour[0][0]
#   |       |       B: contour[0][1]
#   |       |       C: contour[0][2]
#   D-------C       D: contour[0][3]
#
# Rows of cells will be indexed bottom-up:
#   i.e.    contours[0:5] contains all contours in the bottommost row...
#        ...contours[5:10] contains all contours in the next row up...
#        ...contours[n-5:n] contains all contours in the topmost row.
# This holds true because tesseract finds contours from right-to-left bottom-up,
# prioritizing left-ness/right-ness. Because of this, we cannot know for certain
# that the order of each cell relative to its row is correct. In any case, the
# first five contours found will relate to the bottom row of cells, the second
# set of five contours will relate to the next row up, and so on.
#
# This knowledge allows us to search fewer contours to obtain the information
# we need -- the coordinates of both the top-left contour and bottom-right contour.
# Knowing these positions allows us to establish a uniform grid of x/y-coordinates
# which we later use for image slicing.
def grid_info(contours):

    # Get the top-left contour x/y-coordinate
    top_left = (inf, inf)
    for cont in contours[25:30]:
        coord = cont[0][0]
        y = coord[0]
        x = coord[1]
        if (y <= top_left[1]) and (x <= top_left[0]):
            top_left = (y, x)

    # Get the bottom-right contour x/y-coordinate
    bottom_right = (0, 0)
    for cont in contours[0:5]:
        coord = cont[0][0]
        y = coord[0]
        x = coord[1]
        if (y >= bottom_right[1]) and (x >= bottom_right[0]):
            bottom_right = (y, x)

    # Get width & height of an arbitrary contour
    _, _, width, height = cv2.boundingRect(contours[0])


    return top_left, bottom_right, width, height