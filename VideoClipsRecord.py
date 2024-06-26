#file_start_sanity_check
from datetime import datetime
import time
import glob
import cv2

from pathlib import Path
import pathlib

import threading


ALLOWED_FILE_COUNT = 1980
CLIP_IMAGE_LEN = 300
FILE_COUNT_HYSTERESIS = 50

C_font = cv2.FONT_HERSHEY_SIMPLEX
C_bottomLeftCornerOfText = (40, 40)
C_fontScale = 1.3
C_fontColor = (255, 255, 255)
C_thickness = 3
C_lineType = 2


class videoClipsHandler:
    def __init__(self, video_clips_path, camera_name):
        self.video_clips_path = video_clips_path
        self.list_file_cache = []
        self.camera_name = camera_name.strip()
        self.file_count = 0
        self.get_existing_file_list()

        k = datetime.now()
        date_time_str = k.strftime('%Y_%m_%d__%H_%M_%S')
        self.output_video = self.video_clips_path.strip() + self.camera_name +'_'+date_time_str + ".avi"

        self.V_Clip_images_counter = 0
        self.fourcc = cv2.VideoWriter_fourcc(*"MJPG")
        self.img_size_h, self.img_size_w, self.rgb = 480, 640, 3  # img.shape
        self.size = (self.img_size_w, self.img_size_h)
        self.fps = 5  # fps ( = Frames per second)

        self.is_running = False
        self.worker_thread = None



        try:
            self.vid_out = cv2.VideoWriter(self.output_video, self.fourcc, self.fps, self.size, True)
        except:
            self.vid_out = None
            print("!!! Failed to create video clip instance:", {self.output_video})
            pass

        print(f"Initializing videoClipsHandler instance with path: {self.video_clips_path}")
    '''
    def start_worker_thread(self):
        if not self.is_running:
            self.is_running = True
            self.worker_thread = threading.Thread(target=self.worker_function)
            self.worker_thread.start()
            print("Worker thread started.")
        else:
            print("Worker thread is already running.")

    def stop_worker_thread(self):
        if self.is_running:
            self.is_running = False
            self.worker_thread.join()
            print("Worker thread stopped.")
        else:
            print("Worker thread is not running.")
    '''


    def get_existing_file_list(self):
        for file in glob.glob(self.video_clips_path + "/" + "*.avi"):
            self.list_file_cache.append(file)
        self.list_file_cache = sorted(self.list_file_cache) #, reverse=True

        self.file_count = len(self.list_file_cache)
        print ("get_existing_file_list file_count = ",{self.file_count})

    def deleting_old_clips(self):
        count_delete = 0
        while len(self.list_file_cache) > ALLOWED_FILE_COUNT:
            count_delete += 1
            # print("del")
            temp = self.list_file_cache.pop(0)
            print(temp)

            file_to_rem = pathlib.Path(temp)
            try:
                file_to_rem.unlink()
            except:
                print("problem deleting ", temp)
                continue

            print("file deleted = ", count_delete, " - ", temp)
        self.file_count = len(self.list_file_cache)
        print("deleting_old_clips() -  DONE")


    def thread_write_frame_out(self, img, cam_counter, bottomLeftCornerOfText=C_bottomLeftCornerOfText, font=C_font, fontScale=C_fontScale, fontColor=C_fontColor, thickness=C_thickness, lineType=C_lineType):
        k = datetime.now()
        date_time_str = k.strftime('%Y_%m_%d__%H_%M_%S')

        if self.V_Clip_images_counter >= CLIP_IMAGE_LEN:
            # 1.close old video
            if isinstance(self.vid_out, cv2.VideoWriter):
                self.vid_out.release()  # release previous video writer

                # check that the number of files doesn't exceed the limit
                self.file_count += 1
                if self.file_count > ALLOWED_FILE_COUNT+FILE_COUNT_HYSTERESIS:
                    self.deleting_old_clips()


            # 2.create a new video
            self.output_video = self.video_clips_path.strip() + self.camera_name.strip() + '_' + date_time_str + ".avi"
            #Update clip list:
            self.list_file_cache.append(self.output_video)

            try:
                self.vid_out = cv2.VideoWriter(self.output_video, self.fourcc, self.fps, self.size, True)
            except:
                self.vid_out = None
                print("!!! Failed to create video clip instance:", {self.output_video})
                pass

            self.V_Clip_images_counter = 0

        # anyway print time on new received image
        '''
        cv2.putText(img, date_time_str,
                    bottomLeftCornerOfText,
                    font,
                    fontScale,
                    fontColor,
                    thickness,
                    lineType)
        '''

        try:
            self.vid_out.write(img)
        except:
            print("!!! Failed to add an image to video clip:", {self.output_video})
            pass

        self.V_Clip_images_counter += 1
#file_end_sanity_check
