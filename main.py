#!./env/bin/python3
import cv2
import wordle_image_processing as wip
import time

# Get the image
image_path = "./test_images/light1.png"
image = cv2.imread(image_path)

# Make sure it was read properly
if image is None:
    quit("Error: Could not read image.")


print("Analyzing...", end=' ')

# Get guesses from image
s = time.time()
guesses = wip.get_guesses(image)
e = time.time()

print("Finished in %.2fs"%(e-s))
print(guesses)



# test all test images
# for i in range(1, 5):
#     image = cv2.imread(f"./test_images/dark{i}.png")
#     words_from_image(image)
#     image = cv2.imread(f"./test_images/light{i}.png")
#     words_from_image(image)