import cv2
import time
import image_processing
from processing import *
from wait_not_pause import SetWait
import os
import sort_driver

training = True
process = Process("predict")
lev_neu = process.levels
driver = sort_driver.Serial_Driver("COM17")
time.sleep(4)
driver.send({"type": "home"})
# Webcam oeffnen
cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
empty_image = "empty.jpg"
running = False
last_color = ""

# Magazin einrichten
crop = [33,393, 325,413]#[23,408, 328,416]
collect_data_while_sorting = True
feeders_stock = [20,20,20,20] # [76,76,76,76]
wait_time_beteene_feeds = 750 # Abstand zwischen Zufuehrungen
slide_color_to_position_assignment = {"green": 0, "white": 50, "brown": 100}
"""feeders_delay_gross = {
    "1": {"0-9": 70, "10-21": 90, "62-76": 150}, 
    "2": {"0-50": 70, "51-66": 120, "67-76": 140}, 
    "3": {"0-42": 70, "43-52": 95, "53-60": 110, "61-67": 115, "68-73": 125, "74-76": 130 }, 
    "4": {"0-59": 70, "60-64": 90, "65-71": 115, "71-76": 130}, 
}"""
feeders_delay = {
    "1": {"0-5": 120, "6-12": 130, "13-21": 140}, 
    "2": {"0-9": 150, "10-21": 170}, 
    "3": {"0-7": 150, "8-10": 160, "11-21": 180}, 
    "4": {"0-6": 130, "7-17": 150, "18-21": 160}, 
}


delays_for_slide_zones = {"15-30": 100, "31-76": 70, "77-100": 50, "101-139": 20}

free_image_numbers = [None, None, None]

# Rutsche einrichten
slide_pos = 50
colors = ["green", "white", "brown"]
pic_taken = False
current_feeder = 1
feeder_running = False
adjusted = None
feed_time = SetWait(1)
delay_slide_timer = [SetWait(1), False]
delay_slide_far = 650
delay_slide_short = 550
last_detected_color = None
current_detected_color = None 
last_color_send = "white"
print(current_feeder)
take_image = SetWait(3, seconds=True)
#for multiplier in range(2,4):
driver.change_band_data(state= 1, speed= 3000)
#    time.sleep(2)

def handel_feeders():
    global current_feeder
    global feeders_stock
    global feeders_delay
    global feeder_running
    global wait_time_beteene_feeds
    global feed_time
    
    if feeders_stock[current_feeder-1] == 0 and not current_feeder == 4:
        current_feeder += 1
        print("next feeder")
    elif feeders_stock[current_feeder-1] == 0 and current_feeder == 4 and feeder_running: 
        feeder_running = False
        for a in range(1,4):
            for selec in range(0,4):
                driver.feed_it(with_which_one=selec, delay=170)
                time.sleep(0.5)
        print("Done")
    if feeder_running:
        if feed_time.time_up() :
            ranges = [x.split("-") for x in feeders_delay[str(current_feeder)]]
            current_lego = 20 - feeders_stock[current_feeder-1]
            #print("lego:", current_lego, feeders_stock[current_feeder-1], current_feeder)
            for range_values in ranges:
                start, end = [int(x) for x in range_values]
                print(start,end,current_lego)
                if start <= current_lego <= end:
                    delay_time = feeders_delay[str(current_feeder)][str(start) + "-" + str(end)]
                    print("delay:",delay_time)
            print("feed")
            driver.feed_it(with_which_one=current_feeder, delay=delay_time)
            feed_time = SetWait(wait_time_beteene_feeds)
            feeders_stock[current_feeder-1] -= 1 

def handle_slides(move_slide_for_current = False):
    global last_detected_color 
    global current_detected_color 
    global driver
    global delay_slide_timer
    global delay_slide
    global slide_color_to_position_assignment
    global last_color_send
    #print(delay_slide_timer[0].time_up(), delay_slide_timer[1])

    if delay_slide_timer[0].time_up()  and last_detected_color is None and current_detected_color is not None: #and not delay_slide_timer[1]
        driver.send_position(distance_calc(slide_color_to_position_assignment, current_detected_color), 3000) 
        delay_slide_timer[1] = False
        print(last_color_send, current_detected_color)

        if last_color_send == "green" and current_detected_color == "white" or last_color_send == "white" and current_detected_color == "brown" or  last_color_send == "brown" and current_detected_color == "white" or last_color_send == "white" and current_detected_color == "green":
            delay_slide = delay_slide_short
            
        else:
            delay_slide = delay_slide_far
        print("direct: ", current_detected_color, delay_slide) #driver.send_position(distance_calc(slide_color_to_position_assignment, current_detected_color), 3000)
        
        delay_slide_timer[0] = SetWait(delay_slide)
        last_color_send = current_detected_color
        current_detected_color = None
        

    elif not delay_slide_timer[0].time_up() and last_detected_color is None and not last_detected_color ==  current_detected_color:
        print("dleaying", current_detected_color)
        last_detected_color = current_detected_color
        current_detected_color = None
    elif delay_slide_timer[0].time_up() and last_detected_color is not None:
        driver.send_position(distance_calc(slide_color_to_position_assignment, last_detected_color), 3000) 
        #print("delayed: ", last_detected_color) #
        delay_slide_timer[1] = True
        print(last_color_send, last_detected_color)
        if last_color_send == "green" and last_detected_color == "white" or last_color_send == "white" and last_detected_color == "brown" or  last_color_send == "brown" and last_detected_color == "white" or last_color_send == "white" and last_detected_color == "green":
            delay_slide = delay_slide_short
        else:
            delay_slide = delay_slide_far
        print("delayed: ", last_detected_color, delay_slide) #
        delay_slide_timer[0] = SetWait(delay_slide)
        last_color_send = current_detected_color
        last_detected_color = None        
    else: 
        #print("orinf")
        pass
    #print("")

    
def save_image(frame, prediction, accu):
    global free_image_numbers
    if collect_data_while_sorting:
        if free_image_numbers[colors.index(prediction)] is None and os.listdir("collected_images/"+ str(prediction) + "/"):
            print("aouto")
            free_image_numbers[colors.index(prediction)] = max([int(x.replace("image", "").replace(".jpg", "")) for x in os.listdir("collected_images/"+ str(prediction) + "/")]) + 1
        elif not os.listdir("collected_images/"+ str(prediction) + "/"):
            print("non     aouto")
            
            free_image_numbers[colors.index(prediction)] = 0
        text = str(accu)
        position = (10, 10)  # (x, y) position
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.2
        color = (0, 255, 0)  # Green (BGR format)
        thickness = 1
        line_type = cv2.LINE_AA

        # Put text on image
        cv2.putText(frame, text, position, font, font_scale, color, thickness, line_type)
        #cv2.putText(frame, prediction, (10, 30), font, font_scale, color, thickness, line_type)
        cv2.imwrite("collected_images/" + str(prediction) + "/image" + str(free_image_numbers[colors.index(prediction)]) +".jpg", frame)
        free_image_numbers[colors.index(prediction)] += 1  

def distance_calc(slide_color_to_position_assignment, prediction):
    global slide_pos
    pos_to_go = slide_color_to_position_assignment[prediction]
    distance = pos_to_go
    slide_pos = pos_to_go
    return distance

while True:

    ret, frame = cap.read()
    if not pic_taken and take_image.time_up():
        cv2.imwrite("empty.jpg", frame)
        last_frame = empty_band = adjusted = frame[crop[0]:crop[1], crop[2]:crop[3]]
        print(crop, current_feeder)
        pic_taken = True


    handle_slides()
    if pic_taken:
        # Frame aufnehmen
        frame_c = frame[crop[0]:crop[1], crop[2]:crop[3]]
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
        # get color values form image                                   empty_band
        values, cords, average_background = image_processing.get_data(last_frame, frame_c, adjusted, crop)
        
        #wenn es Werte gibt, weiter machen
        if not len(values) == 0 and not len(values[0])  == 0:
            prediction, certainty = process.predict(values)
            #print(cords[0])
            if certainty < 50 and ((prediction == "white" and average_background[1] > 180) or (not prediction == "white" and average_background[1] > 100)):
                process.count_obj_by_position(prediction, cords[0])
            levels = process.levels
            if not lev_neu == levels:
                print(levels)
            lev_neu = levels
            # wenn die erkennung wahrscheinlich richtig ist, dann weiter machen
            if certainty < 50 and not last_color == prediction and ((prediction == "white" and average_background[1] > 150) or (not prediction == "white" and average_background[1] > 100)):
                save_image(frame[crop[0]:crop[1], crop[2]:crop[3]], prediction, certainty) # frame_c um bild mit Erkennungmarkierungen zu speichern
                cv2.imshow("last", frame_c)

                print('\033[94m' + "color: " +  prediction + " certaity: " + str(certainty)  + " info: "+ str(average_background) +'\033[0m')
                current_detected_color = prediction
                handle_slides()# Rutsche aufrufen
                last_color = prediction # erkannte Farbe als lezte speichern
            else:
                pass
            if last_color == prediction:
                #print(prediction, str(certainty))
                pass
        last_frame = frame_c
        if not ret:
            break
            
    #else:
    #    driver.ask_for_data()
    #    response = driver.data_recived
    #    if "buttonState" in response and response["buttonState"]:
    #        running = True
    #        feeder_running = True

    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


cap.release()
cv2.destroyAllWindows()

