import time
import cv2
import numpy as np
from functools import cache
import math

#groeßten Farbkleks finden und zurückgeben
def find_biggest_blob(mask):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        biggest_contour = max(contours, key=cv2.contourArea)

        return biggest_contour

    else:
        return None
def calc_dist_cord(old,new):
    return math.sqrt((int(old[0]) - int(new[0])) ** 2 + (int(old[1]) - int(new[1])) ** 2)

def calc_dist_color(old,new):
    #print(old)
    #print(new)
    dist = math.sqrt((int(old[0]) - int(new[0])) ** 2 + (int(old[1]) - int(new[1])) ** 2 + (int(old[2]) - int(new[2])) ** 2)
    #print(dist)
    return dist 
# Punkte finden und deren Farbwerte zurückgeben
def get_points(image, blob_contour):
    last_point= [0,0]
    cords = []
    x,y = None,None
    cv2.imshow("getpoints",image)
    M = cv2.moments(blob_contour)
    values_at_points = []
    if M["m00"] != 0:
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
        # Punkte auf dem Lego finden 
        points = [(int(cx - 0.35 * (cx - min(blob_contour[:, :, 0].flatten()))), cy),
                  (int(cx + 0.35 * (max(blob_contour[:, :, 0].flatten()) - cx)), cy),
                  (cx, int(cy - 0.35 * (cy - min(blob_contour[:, :, 1].flatten())))),
                  (cx, int(cy + 0.35 * (max(blob_contour[:, :, 1].flatten()) - cy)))]

        for point in points:
            #print(last_point, point, calc_dist(last_point,point))

            if not calc_dist_cord(last_point,point) < 3:
                x, y = point
                if 0 <= x < image.shape[1] and 0 <= y < image.shape[0]:
                    values_at_points.append([value for value in image[y,x]])
                    cords.append(point)
            last_point = point
    #print(values_at_points)
    for x,y in cords:
        cv2.circle(image, (x, y), 3, (0, 255, 0), -1)
    return [image, values_at_points, [y,x]]

def chroma_key(frame, ref, accu):
    ref_color = np.array(ref)
    lower = np.clip(ref_color - accu,0,255)
    upper = np.clip(ref_color + accu,0,255)
    mask = cv2.inRange(frame, lower, upper)
    mask_inv = cv2.bitwise_not(mask)

    obj = cv2.bitwise_and(frame, frame, mask=mask_inv)
    black_background = np.zeros_like(frame)

    final = cv2.add(obj, black_background)
    cv2.imshow("chroma", final)
    return final

def get_data(empty_image, frame, contrast, crop):
    empty_image = empty_image
    #print(empty_image.shape[:2], frame.shape[:2])

    # Differenz der Bilder errechnen

    diff = result = chroma_key(frame, [107, 94, 77], 55)
    cv2.imshow("diff,color", diff)
    diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)

    cv2.imshow("chroma, grey", diff)
    # Schwellenwert anwenden
    _, thresholded = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
    # Konturen finden
    contours, _ = cv2.findContours(thresholded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    cv2.drawContours(result, contours, -1, (255, 255, 255), thickness=cv2.FILLED)
    # Die Maske auf das Bild anwenden

    # Ergebniss in rot gruen und Blau kanäle aufteilen
    blue, green, red = cv2.split(result)
    #print(max(red), min(red))
    #cv2.imshow("red", red)
    #cv2.imshow("result", result)
    #cv2.imshow("mask", mask)
    
    
    # mit Farbwerten schwellenwerte erstllen 
    combined_intensity = np.uint8(np.mean(result, axis=2))

    
    threshold_value = 50
    max_value = 255
    #_, mask = cv2.threshold(combined_intensity, threshold_value, max_value, cv2.THRESH_BINARY)
    #cv2.imshow("mask1", mask)
    _, maskq = cv2.threshold(red, 50, 255, cv2.THRESH_BINARY)
    #cv2.imshow("yellow", maskq)
    #_, blue_mask = 
    # Groeßten Farbkleks finden 

    blob_contour = find_biggest_blob(maskq)
    blob_len = [(len(blob_contour) if blob_contour is not None else 0)] 
    index_of_biggest_blob = blob_len.index(max(blob_len))
    #print(len(index_of_biggest_blob))
    values = [[],[],[]]#[[1,1,1],[1,1,1],[1,1,1]]#
    

    cords = [None, None]#[1,1]#
    """yellow_blob_contour = find_biggest_blob(yellow_mask)
    blue_blob_contour = find_biggest_blob(blue_mask)

    if True:
        if red_blob_contour is not None and index_of_biggest_blob == 0:

            image, values, cords = get_points(frame, red_blob_contour)
            cv2.drawContours(frame, [red_blob_contour], -1, 255, 0)

        elif yellow_blob_contour is not None and index_of_biggest_blob == 1:

            image, values, cords = get_points(frame, yellow_blob_contour)
            cv2.drawContours(frame, [yellow_blob_contour], -1, 255, 0)
    """ 
    #print(blob_contour)               
    if blob_contour is not None:

        image, values, cords = get_points(frame, blob_contour)
        cv2.drawContours(frame, [blob_contour], -1, 255, 0)
     

    #Ergebnisse anzeigen
    cv2.imshow("orig", frame)
    cv2.imshow('Result', result)
    cv2.imshow('contrast', contrast)

    average_color = [[],[]]
    #print(values)
    average_color[0].append([int(rounde) for rounde in cv2.mean(empty_image)[:3]])
    if all(len(sub) > 0 for sub in values) and len(values) > 0:
        #print(values)
        average_color[1] = np.max([calc_dist_color(average_color[0][0],new) for new in values])
    #except Exception as e:
    #    print("errrrror:", values)
    
    #print(average_color)
    return [values, cords, average_color]


