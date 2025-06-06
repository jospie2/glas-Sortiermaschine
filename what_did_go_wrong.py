import cv2
import time
import image_processing
import os
import numpy as np
import json
from numpy import asarray
from numpy import savetxt
import processing
bs = cv2.createBackgroundSubtractorMOG2()
training = True

process = processing.Process("predict")
lev_neu = process.levels
crop = [20,404, 326,412]#[27,404, 326,412]

green_iamges =  os.listdir("collected_images/green")
white_iamges =  os.listdir("collected_images/white")
brown_iamges =  os.listdir("collected_images/brown")
empty_images = ["training_data/empty.jpg"]
print(green_iamges)

def find_biggest_blob(mask):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        biggest_contour = max(contours, key=cv2.contourArea)

        return biggest_contour

    else:
        return None

def get_points(image, blob_contour):
    M = cv2.moments(blob_contour)
    if M["m00"] != 0:
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
        # Define points within the blob, distributed towards the center
        points = [(int(cx - 0.25 * (cx - min(blob_contour[:, :, 0].flatten()))), cy),
                  (int(cx + 0.25 * (max(blob_contour[:, :, 0].flatten()) - cx)), cy),
                  (cx, int(cy - 0.25 * (cy - min(blob_contour[:, :, 1].flatten())))),
                  (cx, int(cy + 0.25 * (max(blob_contour[:, :, 1].flatten()) - cy)))]
        values_at_points = []
        for point in points:
            x, y = point

            if 0 <= x < image.shape[1] and 0 <= y < image.shape[0]:
                values_at_points.append([value for value in image[y,x]])
                print(f"RGB value at ({x}, {y}): {image[y, x]}")
                cv2.circle(image, (x, y), 3, (0, 255, 0), -1)
        print(values_at_points)
        return [image, values_at_points]
color: str = ""
for color_pointer in range(0,3):
    #color_pointer = 2
    print(color_pointer)
    match color_pointer:
        case 0:
            current_images = green_iamges
            path = "collected_images/green/"
            color = "green"
        case 1:
            current_images = white_iamges
            path = "collected_images/white/"
            color = "white"
        case 2:
            current_images = brown_iamges
            path = "collected_images/brown/"
            color = "brown"

    empty_image = cv2.imread("training_data/empty.jpg")[crop[0]:crop[1], crop[2]:crop[3]]
    for image_name in current_images:
        print(image_name)

        frame = cv2.imread(path + image_name)#[crop[0]:crop[1], crop[2]:crop[3]]
        frame_c = frame
        # Bild verarbeiten
        gray_image = cv2.cvtColor(frame_c, cv2.COLOR_BGR2GRAY)
        close_to_black_mask = gray_image < 70
        lab_image = cv2.cvtColor(frame_c, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab_image)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        enhanced_lab_image = cv2.merge((cl, a, b))
        frame_c = cv2.cvtColor(enhanced_lab_image, cv2.COLOR_LAB2BGR)
        alpha = 1.5 # Contrast control (1.0-3.0)
        beta = 10 # Brightness control (0-100)
        adjusted = frame_c 
        # get color values form image
        values, cords, average_background = image_processing.get_data(empty_image, frame_c, adjusted, crop)# show_option=0, last_frame=cv2.imread(empty_image)[crop[0]:crop[1], crop[2]:crop[3]])
        print()
        process.count_obj_by_position(color, cords[0])
        levels = process.levels
        if not lev_neu == levels:
            print(levels)
        lev_neu = levels
            
        print(values)
        prediction, certainty = process.predict(values)
        print(prediction, certainty)
        while not cv2.waitKey(1) & 0xFF == ord('a'):
            pass
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


cv2.destroyAllWindows()
