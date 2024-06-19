# in case of problem importing from google.cloud
# try :  pip install --upgrade google-cloud-storage

'''
Firebase realtime structure:
{
  "cameras": {
    "camera_id_1": {
      "provider_uid": "user_id_1",
      "image_data": "base64_encoded_image_data",
      "timestamp": 1641234567890
    },
    "camera_id_2": {
      "provider_uid": "user_id_2",
      "image_data": "base64_encoded_image_data",
      "timestamp": 1641234568901
    }
  },
  "users": {
    "user_id_1": {
      "cameras": {
        "camera_id_1": true
      }
    },
    "user_id_2": {
      "cameras": {
        "camera_id_2": true
      }
    }
  }
}

Firebase realtime rules:
{
  "rules": {
    "cameras": {
      "$cameraId": {
        ".read": "auth.uid === data.child('provider_uid').val() || root.child('users').child(auth.uid).child('cameras').child($cameraId).exists()",
        ".write": "auth.uid === data.child('provider_uid').val()"
      }
    },
    "users": {
      "$uid": {
        ".read": "$uid === auth.uid",
        ".write": "$uid === auth.uid"
      }
    }
  }
}
'''

import pyrebase
from io import BytesIO
import io
import imageio
import cv2
import numpy as np
import threading
import time

import firebase_admin
from firebase_admin import credentials, storage, db, auth

import hashlib
import uuid

import consts


#from firebase_listener import FirebaseDBListener

import queue
import time

debug_images = 1

def generate_uuid_from_string(input_string):
    # Hash the input string using SHA-256
    hashed_string = hashlib.sha256(input_string.encode()).hexdigest()

    # Use the hashed string to create a UUID
    derived_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, hashed_string)

    return str(derived_uuid)




# Initialize Firebase with your credentials
cred = credentials.Certificate(r'firebase-adminsdk-serviceAccount.json')
firebase_admin.initialize_app(cred, {'storageBucket': 'remotecare-ce82a.appspot.com',
                                     'databaseURL': 'https://remotecare-ce82a.firebaseio.com'})
# Reference to Firebase Storage bucket
bucket = storage.bucket()

# Reference to Firebase Realtime Database
ref = db.reference('/images')

# check basic access to firebase with firebase_admin -> failed
"""
try:
    ref_watchers = db.reference('/cameras').child('96a7ba21-7922-5ed0-aca3-029df2a54cc2').child('curr_watchers')
    ref_send_images_anyway = db.reference('/send_images_anyway')

    # Authenticate using a user's ID token
    user_id_token = 'eyJhbGciOiJSUzI1NiIsImtpZCI6IjAzMmNjMWNiMjg5ZGQ0NjI2YTQzNWQ3Mjk4OWFlNDMyMTJkZWZlNzgiLCJ0eXAiOiJKV1QifQ.eyJuYW1lIjoiSXMiLCJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vcmVtb3RlY2FyZS1jZTgyYSIsImF1ZCI6InJlbW90ZWNhcmUtY2U4MmEiLCJhdXRoX3RpbWUiOjE3MDMwNzk2MDIsInVzZXJfaWQiOiJOTGhnZURUUlV1YkVCRFFDRG1sQ2RqTDJQMlUyIiwic3ViIjoiTkxoZ2VEVFJVdWJFQkRRQ0RtbENkakwyUDJVMiIsImlhdCI6MTcwMzA3OTYwMiwiZXhwIjoxNzAzMDgzMjAyLCJlbWFpbCI6ImJpbnlhbWluYzZAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOmZhbHNlLCJmaXJlYmFzZSI6eyJpZGVudGl0aWVzIjp7ImVtYWlsIjpbImJpbnlhbWluYzZAZ21haWwuY29tIl19LCJzaWduX2luX3Byb3ZpZGVyIjoicGFzc3dvcmQifX0.t3da8IY8PwGVr71gyy2g3h64C2ezH6uuZnbOYNegW7JRNeImg4MqG7Cx9dq0pohfXcizwKFsLNr-PlGmz5EtgdrjULVzOmnyV4jPCmNO11qfLSQ2AybShN5RLfVsMe8KQ_Bv9okCcyuu8oi_1QmHoiviW4glLjY75dfWeVXU61-_WSyoL3LuhMwiU5_GpIbQyhmQFAsAB1haGCRfJsgEGOBCcZJ8wkmVBu8KT4ZmVgQdkToaz4uQNP2kBRdv6FHoovQ7ZpgxD83mu5GoPJUdVhSIGMDkXNtVlcDrAjYY4jkSzkHk7sgjeIUBk4AZrWvFnRClNCm7FJ9a8bUuxf8bYQ'  # "NLhgeDTRUubEBDQCDmlCdjL2P2U2"  # UID for binyaminc6@gmail.com
    authenticated_user = auth.verify_id_token(user_id_token)

    snapshot = ref_watchers.get()
    if snapshot is not None:
        new_value = {"key1": "value1", "key2": "value2"}
        ref_watchers.set(new_value)

except Exception as e:
    print(f"Error setting up stream1: {e}")
"""

class FirebaseDB:
    def __init__(self, config):
        self.config = config
        self.pyrebase = pyrebase.initialize_app(config)
        self.db = self.pyrebase.database()
        self.storage = self.pyrebase.storage()
        self.auth = self.pyrebase.auth()
        self.idToken = None
        # self.refreshToken = None
        # self.localId = None
        # self.expiresIn = None
        self.mail = None
        self.password = None
        self.uid_string_Cam_0 = None

        # Token refreshing thread
        self.refresh_token_thread = threading.Thread(target=self._refresh_token_thread, daemon=True)
        self.refresh_token_thread.start()

        # For firebase_admin interface, because pyrebase is not able to load numpy images (not from disk)
        self.config = config
        self.firebase = pyrebase.initialize_app(config)
        self.db = self.firebase.database()
        self.storage = self.firebase.storage()
        self.firebase_auth = self.firebase.auth()
        
        self.send_images_anyway = False
        self.num_watchers = 1 # was 0
        self.first_time = True

        self.InitializeOnce_updated = False




    def dataBase_init(self, Queue_len ,place_name,camera_name_list):
        place_name = place_name.strip()
        uid_string_place_name = generate_uuid_from_string(place_name)
        #concatanate_all_camera_names:
        res = ""
        for i in range (len (camera_name_list)):
            res = res + camera_name_list[i] + "   "

        data = {
            "place_name": place_name
        }

        self.db = self.pyrebase.database()
        self.db.child('rooms').child(uid_string_place_name)
        self.db.update(data)


        #set general config for a room installation

        data = {
            "Queue_len": str(Queue_len),
            "camera_name_list": res   #.strip()  todo is strip needed ?
        }
        self.db = self.pyrebase.database()
        self.db.child('config')
        self.db.update(data)

        print("Firebase init Done")
        return (uid_string_place_name)

    def user_login(self, uid_string_place_name, mail='hartk111@gmail.com', password="234g2w45jh"):

        if self.firebase is not None:
            # user = auth.sign_in_with_email_and_password(mail, password)
            # TODO: Import a list of all users and relevant cameras for security rules authentication

            try:
                """
                user = auth.create_user(
                    # email=self.mail,
                    email="binyaminc6@gmail.com",
                    email_verified=False,
                    password="123456",
                    display_name="Is",
                    disabled=False
                )
                """
                user = auth.get_user_by_email(mail)

                #uid_user_mail = generate_uuid_from_string(mail)
                uid_user_mail = user.uid
                """
                self.idToken =user.tokens.get("id_token")
                # self.idToken = user['idToken']
                # self.idToken = user.uid

                user_pyre = self.auth.sign_in_with_email_and_password(email="binyaminc6@gmail.com", password="123456")
                # self.idToken = self.auth.create_custom_token(user.uid)
                self.idToken = user_pyre['idToken']
                print(self.idToken)
                uid = user.uid
                """
                #add new user to same only one camera in project
                data = {
                    uid_string_place_name: True
                }

                self.db = self.pyrebase.database()
                self.db.child('users').child(uid_user_mail)
                self.db.update(data)

            except Exception as e:
                print(f"Error is: {e}")

        else:
            print("firebase not initialized correctly, so login failed")
            return None

        #return uid


    def _refresh_token_thread(self):
        while True:
            self.firebase = pyrebase.initialize_app(self.config)  # Replace with your actual Firebase configuration
            self.db = self.firebase.database()
            self.storage = self.firebase.storage()
            self.auth = self.firebase.auth()

            '''
            user = self.auth.sign_in_with_email_and_password(self.mail, self.password)
            if user:
                self.idToken = user["idToken"]

            print("Token refresh cycle started")
            '''
            time.sleep(55 * 60)  # Refresh the token every 40 minutes

    def firebase_admin_upload_np_image_to_storage(self, person_count, opencv_image, filename, datetime,uid_string_place_name, camera_name, rect_data, speed,
                                                  camera_block, camera_block_percentage_top, camera_block_percentage_bottom, width, hight):

        '''cv2.putText(opencv_image, datetime,
                    consts.C_bottomLeftCornerOfText_small,
                    consts.C_font,
                    consts.C_fontScale/4,
                    consts.C_fontColor_black,
                    consts.C_thickness_8,
                    consts.C_lineType)
        '''
        if person_count>0:
            cv2.putText(opencv_image, datetime,
                        consts.C_bottomLeftCornerOfText_small,
                        consts.C_font,
                        0.4, #consts.C_fontScale/4,
                        consts.C_fontColor,
                        1, #consts.C_thickness_4/4,
                        consts.C_lineType)


        if self.InitializeOnce_updated == False:
            self.db = self.pyrebase.database()
            self.db.child('rooms')

            self.db.update({
                'InternetSpeed': speed
            })

            if camera_block.strip()=='bottom':
                block_percentage_bottom = int(camera_block_percentage_bottom.strip())
                if block_percentage_bottom > 0:
                    #0_371_790_378_ 790_541_1_537_0_371
                    btm_up = int(hight*(1-block_percentage_bottom/100))
                    filter_string = '0_'+str(btm_up)+'_'+str(width)+'_'+str(btm_up)+'_'+str(width)+'_'+str(hight)+'_'+'0_'+str(hight)+'_'+'0_'+str(btm_up)
                    print('filter_string = ',filter_string)

                    self.db = self.pyrebase.database()
                    self.db.child('rooms').child(uid_string_place_name).child(camera_name+"_mask")
                    self.db.update({
                        '0': filter_string
                    })

            if camera_block.strip()=='ceiling':
                block_percentage_bottom = int(camera_block_percentage_top.strip())
                if block_percentage_bottom > 0:
                    #0_0_800_0_800_200_0_200_0_0
                    ceil_dn = int(hight*(block_percentage_bottom/100))
                    filter_string = '0_0_'+str(width)+'_0_'+str(width)+'_'+str(ceil_dn)+'_'+'0_'+str(ceil_dn)+'_'+'0_0'
                    print('filter_string = ',filter_string)

                    self.db = self.pyrebase.database()
                    self.db.child('rooms').child(uid_string_place_name).child(camera_name+"_mask")
                    self.db.update({
                        '1': filter_string
                    })

            if camera_block.strip() == 'both':
                block_percentage_bottom = int(camera_block_percentage_bottom.strip())
                if block_percentage_bottom > 0:
                    # 0_371_790_378_ 790_541_1_537_0_371
                    btm_up = int(hight * (1 - block_percentage_bottom / 100))
                    filter_string = '0_' + str(btm_up) + '_' + str(width) + '_' + str(btm_up) + '_' + str(
                        width) + '_' + str(hight) + '_' + '0_' + str(hight) + '_' + '0_' + str(btm_up)
                    print('filter_string = ', filter_string)

                    self.db = self.pyrebase.database()
                    self.db.child('rooms').child(uid_string_place_name).child(camera_name + "_mask")
                    self.db.update({
                        '0': filter_string
                    })

                block_percentage_bottom = int(camera_block_percentage_top.strip())
                if block_percentage_bottom > 0:
                    # 0_0_800_0_800_200_0_200_0_0
                    ceil_dn = int(hight * (block_percentage_bottom / 100))
                    filter_string = '0_0_' + str(width) + '_0_' + str(width) + '_' + str(ceil_dn) + '_' + '0_' + str(
                        ceil_dn) + '_' + '0_0'
                    print('filter_string = ', filter_string)

                    self.db = self.pyrebase.database()
                    self.db.child('rooms').child(uid_string_place_name).child(camera_name + "_mask")
                    self.db.update({
                        '1': filter_string
                    })

            self.InitializeOnce_updated = True


        if speed == "High":

            # Convert OpenCV image to bytes
            _, image_data = cv2.imencode('.jpg', opencv_image)

            # Create an in-memory binary stream
            image_stream = io.BytesIO(image_data)

            # Reference to the Firebase Storage bucket
            firebase_admin_bucket = storage.bucket()

            # Create a blob (file) in the bucket
            storage_bucket = f'images/'+uid_string_place_name+'/'+camera_name+'/'+filename
            blob = firebase_admin_bucket.blob(storage_bucket)

            # Upload the image data to the blob
            blob.upload_from_file(image_stream, content_type='image/jpeg')

            blob.make_public()

            # Get the download URL of the uploaded image
            download_url = blob.public_url

            self.db = self.pyrebase.database()
            self.db.child('rooms').child(uid_string_place_name).child(camera_name)
            if debug_images == 1:
                download_url_split = download_url.split("/")
            try:
                if debug_images==1:
                    rect_data = rect_data + '_'+ download_url_split[-1]
                    rect_data = rect_data.split('.')[0]

                self.db.update({
                    'image_data': download_url,
                    'timestamp': datetime,
                    'rect_data': rect_data
                    })
            except Exception as e:
                print(f"Error in db.update: {e}")
        elif speed=="Low":
            #upload just rect corners. And an image every 2 hours without persons

            self.db = self.pyrebase.database()
            self.db.child('rooms').child(uid_string_place_name).child(camera_name+'_empty_Img')
            self.db.update({
                camera_name + '_empty_Img' : ""
            })

            self.db = self.pyrebase.database()
            self.db.child('rooms').child(uid_string_place_name).child(camera_name)
            if debug_images == 1:
                download_url_split = download_url.split("/")
            try:
                if debug_images == 1:
                    rect_data = rect_data + '_' + download_url_split[-1]
                    rect_data = rect_data.split('.')[0]

                self.db.update({
                    'image_data': download_url,
                    'timestamp': datetime,
                    'rect_data': rect_data
                })
            except Exception as e:
                print(f"Error in db.update: {e}")

        return download_url

    def handler1(self, message):
        self.num_watchers = message['data']
        print(f"updated number of watchers: {self.num_watchers}")

    def has_watchers(self):
        return self.num_watchers > 0 or self.send_images_anyway


# Usage example
if __name__ == "__main__":
    # Replace with your actual Firebase configuration

    config = {
        "apiKey": "AIzaSyCpWjvONF2eLfIxsFOKSJaM8oU4HvLiW-M",
        "authDomain": "480830608258-hsnsgpgooeov6v0cqdhcn5ba9ccqdg3g.apps.googleusercontent.com",
        "databaseURL": "https://remotecare-ce82a-default-rtdb.firebaseio.com",
        "storageBucket": "remotecare-ce82a.appspot.com",
        "serviceAccount": r"firebase-adminsdk-serviceAccount.json"
    }

    # Initialize FirebaseDB instance
    firebase_db = FirebaseDB(config, "shlomocohen2@gmail.com", "123456")

    image_path = "C://projects//yolov7_custom//yolov7//data//saba_regular//frame_1502.jpg"
    image_name_in_firebase = image_path.split('//')[-1]

    NP_image = cv2.imread(image_path)

    return_url = firebase_db.firebase_admin_upload_np_image_to_storage(NP_image, "NP_frame_1502.jpg")

    # Get data from database
    # result = firebase_db.get_data("example/path")
