#file_start_sanity_check
# pyinstaller --onefile --paths="C:\Python\Python3.8.8\Lib\site-packages\cv2" main.py
import os
import cv2
import numpy as np
from ultralytics import YOLO
from threading import Thread
import threading
import os

token = r"https://docs.google.com/document/d/1UsUR0mj6AfyEyK42Q1yhRJfVIW8QNYSEs-ULIz1LwHk/edit?usp=sharing"

# from Internet_SpeedTest import check_speed
from VideoClipsRecord import videoClipsHandler
from send_data_to_app_via_firebase import FirebaseDB
from datetime import datetime
import time

import consts


# from compute_ssi_diff import compute_ssi_diff

# Define the threshold
THRESHOLD = 0.45

# Define the blurring kernel
BLUR_KERNEL = (61, 61)  # 101, 101  / 81,81

print_timing = 0

do_internetSpeedCheck = 0

do_restart_PC_Once = 0

# if do_internetSpeedCheck:
#    down, up = check_speed()

if print_timing:
    if print_timing:    start = time.process_time()

# Load the YOLOv8 model
model = YOLO("yolov8l.pt")
# model = YOLO("yolov8s.pt") #was the net

if print_timing:
    elapsed_time = time.process_time() - start
    print("YOLO upload elapsed_time = ", elapsed_time)


# Creating an instance of videoClipsHandler
#videoClipsHandlerInst = videoClipsHandler(r"C:\\projects\\check_clips_records")

config = {
    "apiKey": "AIzaSyCpWjvONF2eLfIxsFOKSJaM8oU4HvLiW-M",
    "authDomain": "480830608258-hsnsgpgooeov6v0cqdhcn5ba9ccqdg3g.apps.googleusercontent.com",
    "databaseURL": "https://remotecare-ce82a-default-rtdb.firebaseio.com",
    "storageBucket": "remotecare-ce82a.appspot.com",
    "serviceAccount": r"firebase-adminsdk-serviceAccount.json"
}

# read config file
file1 = open('config.txt', 'r')
Lines = file1.readlines()
count = 0
show_on_screen = 0  # don't show
video_dir = r"C:\projects\check_clips_records\\"
firebase_queue_len = 50  # default
place_name = "location"
camera_name_list = []
camera_block_list = []
camera_block_percentage = []
total_cameras = 1

for line in Lines:
    count += 1
    # print("Line{}: {}".format(count, line.strip()))
    print("line =", line)
    line_split = line.strip().split(" ")
    if line_split[0] == "show_on_screen":
        show_on_screen = int(line_split[-1].strip())
    if line_split[0] == "video_dir":
        video_dir = line_split[-1]
    if line_split[0] == "firebase_queue_len":
        firebase_queue_len = int(line_split[-1].strip())
    if line_split[0] == "place_name":
        place_name = line_split[-1]
    if line_split[0] == "total_cameras":
        total_cameras = int(line_split[-1].strip())
    if line_split[0] == "camera_name":
        for cam_idx in range(total_cameras):
            camera_name_list.append((line_split[cam_idx + 1]).strip())
    if line_split[0] == "camera_block_percentage":
        for cam_idx in range(total_cameras):
            camera_block_percentage.append(line_split[cam_idx*2 + 1])
            camera_block_percentage.append(line_split[cam_idx*2 + 2])
    if line_split[0] == "camera_block_bottom_ceiling_both":
        for cam_idx in range(total_cameras):
            camera_block_list.append(line_split[cam_idx + 1])





    if line_split[0] == "print_timing":
        print_timing = int(line_split[-1].strip())
    if line_split[0] == "do_internetSpeedCheck":
        do_internetSpeedCheck = int(line_split[-1].strip())
    if line_split[0] == "internet_speed_Low_Mid_High":
        internet_speed_Low_Mid_High = line_split[-1]  # "Low" or "Mid" or "High"

if do_internetSpeedCheck:
    down, up = check_speed()

videoClipsHandlerInstances = []
cap_list = []
# Load the video
for cam_num in range(total_cameras):
    cap_list.append(cv2.VideoCapture(cam_num))

# Creating an instance of videoClipsHandler
for i in range(total_cameras):
    videoClipsHandlerInstances.insert(i, videoClipsHandler(video_dir, camera_name_list[i]))

uid_string_place_name = "1717"
uid_string_camera_name = "1818"

succeded = False
while not succeded:
    try:
        # Initialize FirebaseDB instance
        firebase_db_Inst = FirebaseDB(config)
        uid_string_place_name = firebase_db_Inst.dataBase_init(firebase_queue_len, place_name, camera_name_list)
        firebase_db_Inst.user_login(uid_string_place_name, "shlomocohen3@gmail.com", "123456")
        #firebase_db_Inst.user_login(uid_string_place_name, "google_tester@gmail.com", "123456")
        succeded = True
    except Exception as e:
        print(f"Error in Initialize FirebaseDB instance: {e}")


def downsize_and_gray_image(image, factor, cnvrt_to_grey=1):
    # Check if the image is loaded successfully
    if image is None:
        print("Image to downsize empty")
        return None

    # Get the original width and height
    original_width, original_height = image.shape[1], image.shape[0]

    # print("original_width, original_height = ",original_width, original_height)

    # Calculate new width and height as half of the original dimensions
    new_width = int(original_width / factor)  # was 2
    new_height = int(original_height / factor)  # was 2

    # Resize the image
    resized_image = cv2.resize(image, (new_width, new_height))

    # Convert the resized image to grayscale
    if cnvrt_to_grey == 1:
        grayscale_image = cv2.cvtColor(resized_image, cv2.COLOR_BGR2GRAY)
        return grayscale_image
    else:
        width, height = resized_image.shape[1], resized_image.shape[0]
        print("resized_image_width, resized_image_height = ", width, height)
        return resized_image


def detect_person(frame):
    # Make a prediction

    if print_timing:    start = time.process_time()

    # frame = downsize_and_gray_image(frame, 2, 0)  # 0 -dont convert to grey

    detections = model(frame, classes=[0])  # added [0] to select persons only
    if print_timing: Elapsed_time = time.process_time() - start
    if print_timing:  check = "333333 - 111111111****************************detect_person_run model" + " = " + str(
        Elapsed_time)
    if print_timing:  print(check)

    if print_timing:    start = time.process_time()
    # Filter out detections with a low confidence score
    filtered_detections = []
    for box in detections[0].boxes:
        if box.conf is not None and box.conf.numel() > 0:  # Check if probs is not None and not empty
            max_prob = box.conf.max().item()  # Get the maximum probability
            if max_prob >= THRESHOLD and box.cls[0] == 0:
                filtered_detections.append([box.xywh.tolist()[0], box.conf.max().item()])

    if print_timing: Elapsed_time = time.process_time() - start
    if print_timing: check = "333333 - 222222222****************************detect_person_Do filtering_" + " = " + str(
        Elapsed_time)
    if print_timing: print(check)

    # Return the filtered detections
    return filtered_detections


# PC restart
def restart():
    os.system("shutdown /r /t 0")


def blurring_rectangle(frame, top_left_x, top_left_y, bottom_right_x, bottom_right_y):
    #new_frame = frame.copy()
    subimage = frame[top_left_y:bottom_right_y, top_left_x:bottom_right_x]
    blurred_subimage = cv2.GaussianBlur(subimage, BLUR_KERNEL, 0)
    frame[top_left_y:bottom_right_y, top_left_x:bottom_right_x] = blurred_subimage
    return frame


def check_person_distance(bounding_box, LastBoundingBox):
    LOCATION_OFFSET = 25
    # check cur_x-Last_x
    if abs(bounding_box[0] - LastBoundingBox[0]) > LOCATION_OFFSET:
        return True, 'x', abs(bounding_box[0] - LastBoundingBox[0])
    if abs(bounding_box[1] - LastBoundingBox[1]) > LOCATION_OFFSET:
        return True, 'y', abs(bounding_box[1] - LastBoundingBox[1])
    if abs(bounding_box[2] - LastBoundingBox[2]) > LOCATION_OFFSET:
        return True, 'w', abs(bounding_box[2] - LastBoundingBox[2])
    if abs(bounding_box[3] - LastBoundingBox[3]) > LOCATION_OFFSET:
        return True, 'h', abs(bounding_box[3] - LastBoundingBox[3])

    return False, '_', 0


def main():
    error_counter = 0
    # TO ENABLE last image upload to F.B. as empty image from humans
    motion_count_down = []
    motion_count_down = [1 for i in range(total_cameras)]

    image_empty_from_humans = []
    image_empty_from_humans = [1 for i in range(total_cameras)]

    cam_counter = 0
    image_counter = 0
    # last_frame = None
    last_frame = []
    curr_frame = []
    blured_frame = []
    image_counter = []
    filtered_detections = []
    send_to_Firebase = False

    # Add time stamp on images
    '''
    C_font = cv2.FONT_HERSHEY_SIMPLEX
    C_bottomLeftCornerOfText = (20, 460)
    C_fontScale = 1.3
    C_fontColor = (255, 255, 255)
    C_fontColor_black = (0, 0, 0)
    C_thickness_8 = 8
    C_thickness_4 = 4
    C_lineType = 2
    '''

    Last_time_No_Person_in_image = []

    LastFiltered_detections = [[0, 0, 0, 0] for i in range(total_cameras)]
    last_found_persons = []

    for i in range(total_cameras):
        if print_timing:    start = time.process_time()
        ret, frame = cap_list[cam_counter].read()
        if print_timing: Elapsed_time_get_pictue = time.process_time() - start
        if print_timing:  check = "**************************************Elapsed_time_get_picture_" + str(
            i) + " = " + str(Elapsed_time_get_pictue)
        if print_timing:  print(check)

        frame_grey = downsize_and_gray_image(frame, 4)
        blurred_frame = cv2.GaussianBlur(frame_grey, (17, 17), 0)  #WAS 21,21
        last_frame.insert(i, blurred_frame)
        curr_frame.insert(i, blurred_frame)
        image_counter.insert(i, 0)  # create an image counter per camera
        blured_frame.insert(i, blurred_frame)
        last_found_persons.insert(i, 0)
        # LastFiltered_detections[i] = [0,0,0,0]  #xywh

        start_time = time.time()
        Last_time_No_Person_in_image.insert(i, start_time)

    # Loop over the frames in the video
    while True:
        # Get system time
        k = datetime.now()
        date_time_str = k.strftime('%H:%M:%S  %d/%m/%Y')
        time_split = date_time_str.split(' ')[0].split(':')

        # restart the PC every night at 03:07
        if 2 < int(time_split[0]) < 4 and 6 < int(time_split[1]) < 12:
            print("Do Restart")
            ### restart() #################################################### TEMPORARY removed for debugging android

        send_to_Firebase = False

        # Capture the next frame
        cam_counter += 1
        cam_counter = cam_counter % total_cameras

        if print_timing:    start = time.process_time()
        ret, curr_frame[cam_counter] = cap_list[cam_counter].read()
        if print_timing:  Elapsed_time = time.process_time() - start
        if print_timing:  check = "**************************************Elapsed_time_get_pictue_" + str(
            cam_counter) + " = " + str(Elapsed_time)
        if print_timing:  print(check)

        # If the frame is empty, break out of the loop
        if not ret:
            error_counter += 1
            error_counter = error_counter % 300
            # sendError2Firebase(error_counter, str(cam_counter) + ' : ' + "No image")
            continue

        if print_timing:    start = time.process_time()
        frame_grey = downsize_and_gray_image(curr_frame[cam_counter], 1)  # was 4
        if print_timing: Elapsed_time = time.process_time() - start
        if print_timing:  check = "1111111****************************Elapsed_time_frame_grey_" + str(
            cam_counter) + " = " + str(Elapsed_time)
        if print_timing:  print(check)

        # check if the image is bright enough
        if print_timing:    start = time.process_time()
        bool_image_lit, average_brightness = is_image_lit(frame_grey, grid_size=(10, 10), brightness_threshold=15)  # 80
        print(f"is image lit: {bool_image_lit}. (average brightness = {average_brightness}")
        if print_timing: Elapsed_time = time.process_time() - start
        if print_timing: check = "2222222****************************Elapsed_time_is_image_lit_" + str(
            cam_counter) + " = " + str(Elapsed_time)
        if print_timing: print(check)

        if not bool_image_lit:
            print("Not uploading to firebase. Brightness is too low")
            error_counter += 1
            error_counter = error_counter % 100
            # sendError2Firebase(error_counter, str(cam_counter) + ' : ' + "Low light")
            continue

        # cv2.imwrite(r'C:\\projects\\check_clips_records\\check_input_to_diff\\last.jpg', last_frame[cam_counter])
        # cv2.imwrite(r'C:\\projects\\check_clips_records\\check_input_to_diff\\blurred_frame_.jpg', frame_grey)

        last_frame[cam_counter] = frame_grey

        # write sample images to disk
        # file_path = "C:/projects/check_clips_records/check_frames/" + str(image_counter) + ".jpg"
        # cv2.imwrite(file_path,frame)
        # image_counter+=1

        if print_timing:    start = time.process_time()
        # Detect persons in the frame


        filtered_detections = detect_person(curr_frame[cam_counter])
        if print_timing: Elapsed_time = time.process_time() - start
        if print_timing: check = "333333****************************detect_person_" + str(cam_counter) + " = " + str(
            Elapsed_time_get_pictue)
        if print_timing:  print(check)

        # if found person in image: try not to stop show until no person are in image
        motion_count_down[cam_counter] = 2

        # Save image after masking all persons
        pers_count = 0
        person_count = len(filtered_detections)

        rect_data = "_"

        if len(filtered_detections) > 1:  # more than one person
            send_to_Firebase = True  # send anyway

        if last_found_persons[cam_counter] >= 1 and len(filtered_detections) == 0:
            send_to_Firebase = True

            last_found_persons[cam_counter] = 0
            error_counter += 1
            error_counter = error_counter % 100
            # sendError2Firebase(error_counter, str(cam_counter) + ' : ' + "No Person")

        blured_frame[cam_counter] = curr_frame[cam_counter].copy()
        # Draw bounding boxes around the filtered detections
        for detection in filtered_detections:
            confidence_score = detection[1]

            # Get the bounding box of the detection
            bounding_box = detection[0]  # bounding_box is a list of four floats: [x1, y1, w, h]

            # Convert the bounding box to two points
            top_left_x = int(bounding_box[0] - bounding_box[2] // 2)
            top_left_y = int(bounding_box[1] - bounding_box[3] // 2)
            bottom_right_x = int(bounding_box[0] + bounding_box[2] // 2)
            bottom_right_y = int(bounding_box[1] + bounding_box[3] // 2)

            if LastFiltered_detections[cam_counter] == None:
                send_to_Firebase = True

            last_found_persons[cam_counter] = 1

            if send_to_Firebase == False:
                if print_timing:    start = time.process_time()
                send_to_Firebase, who, diff = check_person_distance(bounding_box, LastFiltered_detections[cam_counter])
                print("send_to_Firebase = ", send_to_Firebase, ' param = ', who, ' diff =', diff)
                if print_timing: Elapsed_time = time.process_time() - start
                if print_timing:  check = "555555****************************check_person_distance_" + str(
                    cam_counter) + " = " + str(
                    Elapsed_time_get_pictue)
                if print_timing:  print(check)

            LastFiltered_detections[cam_counter] = bounding_box

            rect_data += str(int(bounding_box[0])) + "_" + str(int(bounding_box[1])) + "_" + str(
                int(bounding_box[2])) + "_" + str(int(bounding_box[3])) + "_"

            # Draw a rectangle around the detection
            if print_timing:
                start = time.process_time()
            cv2.rectangle(blured_frame[cam_counter], (top_left_x, top_left_y), (bottom_right_x, bottom_right_y),
                          (255, 255, 255), 2)

            # Print the confidence score of the detection over the screen
            cv2.putText(blured_frame[cam_counter], f"{confidence_score:.2f}", (top_left_x, top_left_y - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)

            if print_timing: Elapsed_time = time.process_time() - start
            if print_timing:  check = "6666666****************************cv2.rectangle + cv2.putText_" + str(
                cam_counter) + " = " + str(
                Elapsed_time_get_pictue)
            if print_timing:  print(check)

            # mask person appearance
            # cv2.rectangle(frame, (top_left_x, top_left_y), (bottom_right_x, bottom_right_y), (0, 0, 0), -1)
            curr_frame_shape = curr_frame[cam_counter].shape
            # print(curr_frame_shape)

            if print_timing:    start = time.process_time()
            blured_frame[cam_counter] = blurring_rectangle(blured_frame[cam_counter], top_left_x, top_left_y,
                                                         bottom_right_x, bottom_right_y)
            if print_timing: Elapsed_time = time.process_time() - start
            if print_timing:  check = "77777777****************************blurring_rectangle_" + str(
                cam_counter) + " = " + str(
                Elapsed_time_get_pictue)
            if print_timing:  print(check)

            # if needs to record frame, send to dedicated thread
            if pers_count >= person_count - 1:
                # append image to clip
                # frame_grey = downsize_and_gray_image(frame, 2) # not creating a video that can be opened
                if print_timing:    start = time.process_time()

                timed_curr_frame = curr_frame[cam_counter].copy()
                cv2.putText(timed_curr_frame, date_time_str,
                            consts.C_bottomLeftCornerOfText,
                            consts.C_font,
                            consts.C_fontScale,
                            consts.C_fontColor_black,
                            consts.C_thickness_8,
                            consts.C_lineType)

                cv2.putText(timed_curr_frame, date_time_str,
                            consts.C_bottomLeftCornerOfText,
                            consts.C_font,
                            consts.C_fontScale,
                            consts.C_fontColor,
                            consts.C_thickness_4,
                            consts.C_lineType)



                t_writer = threading.Thread(
                    target=videoClipsHandlerInstances[cam_counter].thread_write_frame_out(timed_curr_frame,
                                                                                          cam_counter))
                if print_timing: Elapsed_time = time.process_time() - start
                if print_timing:  check = "8888888****************************videoClipsHandlerInst.thread_write_frame_out_" + str(
                    cam_counter) + " = " + str(
                    Elapsed_time)
                if print_timing:  print(check)
            else:
                pers_count += 1




        image_counter[cam_counter] += 1
        if image_counter[cam_counter] > firebase_queue_len:
            image_counter[cam_counter] = 1
        img_name = str(image_counter[cam_counter]) + '.jpg'

        frame_grey_4_video = downsize_and_gray_image(curr_frame[cam_counter], 4)
        #k = datetime.now()
        #date_time_str = k.strftime('%H:%M:%S %d/%m/%Y')

        ############################################
        rect_data = str(person_count) + rect_data[:-1]

        # if bool_image_lit and has_motion:
        try:
            if send_to_Firebase == True:

                cv2.putText(blured_frame[cam_counter], date_time_str,
                            consts.C_bottomLeftCornerOfText,
                            consts.C_font,
                            consts.C_fontScale,
                            consts.C_fontColor_black,
                            consts.C_thickness_8,
                            consts.C_lineType)

                cv2.putText(blured_frame[cam_counter], date_time_str,
                            consts.C_bottomLeftCornerOfText,
                            consts.C_font,
                            consts.C_fontScale,
                            consts.C_fontColor,
                            consts.C_thickness_4,
                            consts.C_lineType)

                frame_grey = downsize_and_gray_image(blured_frame[cam_counter], 4)
                width,hight = curr_frame[cam_counter].shape[1], curr_frame[cam_counter].shape[0]
                if print_timing:    start = time.process_time()
                t_writer = threading.Thread(
                    target=firebase_db_Inst.firebase_admin_upload_np_image_to_storage(person_count,frame_grey, img_name,
                                                                                      date_time_str,
                                                                                      uid_string_place_name,
                                                                                      str(cam_counter), rect_data,
                                                                                      internet_speed_Low_Mid_High,
                                                                                      camera_block_list[cam_counter],
                                                                                      camera_block_percentage[cam_counter * 2],
                                                                                      camera_block_percentage[cam_counter * 2 + 1],
                                                                                      width,
                                                                                      hight
                                                                                      ))
                if print_timing: Elapsed_time = time.process_time() - start
                if print_timing:  check = "9999999****************************firebase_db_Inst.firebase_admin_upload_np_image_to_storage_" + str(
                    cam_counter) + " = " + str(
                    Elapsed_time_get_pictue)
                if print_timing:  print(check)




        except Exception as e:
            print(f"Error is: {e}")

        if show_on_screen:

            cv2.putText(blured_frame[cam_counter], date_time_str,
                        consts.C_bottomLeftCornerOfText,
                        consts.C_font,
                        consts.C_fontScale,
                        consts.C_fontColor_black,
                        consts.C_thickness_8,
                        consts.C_lineType)




            cv2.putText(blured_frame[cam_counter], date_time_str,
                        consts.C_bottomLeftCornerOfText,
                        consts.C_font,
                        consts.C_fontScale,
                        consts.C_fontColor,
                        consts.C_thickness_4,
                        consts.C_lineType)

            if print_timing:    start = time.process_time()
            # Display the frame
            name = "Cam_" + str(cam_counter)

            cv2.imshow(name, blured_frame[cam_counter])
            if print_timing: Elapsed_time = time.process_time() - start
            if print_timing:  check = "10101010****************************cv2.imshow_" + str(
                cam_counter) + " = " + str(Elapsed_time_get_pictue)
            if print_timing:  print(check)

            # Check for the "q" key to quit the loop
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    # Release the video capture object and close the OpenCV window

    for cam_num in range(total_cameras):
        cap_list[cam_num].release()
    cv2.destroyAllWindows()


def check_image_motion(last_image, curr_image, similarity_threshold=170):  # was 10

    if last_image is None:
        return True, -1

    # calculate Mean Square Error
    err = np.sum((last_image.astype("float") - curr_image.astype("float")) ** 2)
    err /= float(last_image.shape[0] * last_image.shape[1])

    return err > similarity_threshold, err


def sample_grid_pixels(image, grid_size):
    height, width = image.shape[:2]

    # Initialize an empty list to store sampled pixel values
    sampled_pixels = []

    grid_size_x, grid_size_y = grid_size

    for i in range(grid_size_x):
        for j in range(grid_size_y):
            # Calculate pixel coordinates based on grid size
            row = int((height - 1) * i / (grid_size_x - 1))
            col = int((width - 1) * j / (grid_size_y - 1))

            # Sample the pixel value at the calculated coordinates
            pixel_value = image[row, col]

            # Append the sampled pixel value to the list
            sampled_pixels.append(pixel_value)

    return sampled_pixels


def is_image_lit(image, grid_size, brightness_threshold):
    # Sample pixel values using a grid pattern
    sampled_pixels = sample_grid_pixels(image, grid_size)

    # Calculate the average pixel value
    average_pixel_value = np.mean(sampled_pixels)

    # Check if the average is beyond the threshold
    return (average_pixel_value > brightness_threshold), average_pixel_value


if __name__ == "__main__":
    main()
#file_end_sanity_check
