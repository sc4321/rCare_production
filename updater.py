#file_start_sanity_check
import time
from datetime import datetime

import requests
import subprocess  # For secure updates using Git
from datetime import datetime, timedelta  # For scheduling daily checks
import os
import shutil
import stat  # Import the stat module
import platform
from send_data_to_app_via_firebase import generate_uuid_from_string
from send_data_to_app_via_firebase import FirebaseDB

config = {
    "apiKey": "AIzaSyCpWjvONF2eLfIxsFOKSJaM8oU4HvLiW-M",
    "authDomain": "480830608258-hsnsgpgooeov6v0cqdhcn5ba9ccqdg3g.apps.googleusercontent.com",
    "databaseURL": "https://remotecare-ce82a-default-rtdb.firebaseio.com",
    "storageBucket": "remotecare-ce82a.appspot.com",
    "serviceAccount": r"firebase-adminsdk-serviceAccount.json"
}

firebase_db_Inst = FirebaseDB(config)

'''
    def FB_Log(LogDate, LogString,uid_string_place_name):
        self.db = self.pyrebase.database()
        self.db.child('rooms').child(uid_string_place_name).child('Log')
        data = LogDate + ":" + LogString
        self.db.update(data)
'''

def get_place_name():
    # read config file
    file1 = open('config.txt', 'r')
    Lines = file1.readlines()
    for line in Lines:
        line_split = line.strip().split(" ")
        if line_split[0] == "place_name":
            print("line =", line)
            place_name = line_split[-1]
            break
    return place_name

place_name = get_place_name()
uid_string_place_name = generate_uuid_from_string(place_name)

def Log(LogDate, LogString):
    firebase_db_Inst.FB_Log(LogDate, LogString, uid_string_place_name)



# GitHub repository URL
repo_url = "https://api.github.com/repos/sc4321/rCare_production"
repo_cloning_url = "https://github.com/sc4321/rCare_production.git"

# Last update file path
LAST_UPDATE_FILE = "./last_updated_time.txt"
CLONED_FOLDER_PATH = "./updated_project"
TMP_FOLDER = r"c:/tmp/rCare/"
BACKUP_FOLDER = "../production_back"
START_COPY_VERSION_FILE_NAME = "./version_start_copy.txt"
END_COPY_VERSION_FILE_NAME = "./version_end_copy.txt"

# Update check interval (in days)
UPDATE_INTERVAL = 1

# Magic numbers:
REQUEST_HAS_SUCCEEDED = 200
RETRIES_FOR_INTERNET_FAILURE = 10
RETRIES_FOR_CLONING_FAILURE = 10

FILE_NAMES_TO_CHECK = {"./updater.py", "./main.py","./config.txt","./run.bat","./VideoClipsRecord.py","./VideoClipsRecord.py","./consts.py"}

def check_all_files_are_valid(file_list):

    for file_name in file_list:
        try:
            file = open(file_name, 'r')
            lines = file.readlines()
            ext = file_name.split(".")[-1]

            if ext == "py" or ext == "txt":
                check_start = lines[0].strip()
                check_end = lines[-1].strip()

                if lines[0].strip() == "#file_start_sanity_check" and lines[-1].strip() == "#file_end_sanity_check":
                    print(file_name, " is OK")
                    file.close()
                else:
                    print(file_name, " is NOT OK")
                    file.close()
                    return False    # problem occurred

            if ext == "bat":
                if lines[0].strip() == "REM file_start_sanity_check" and lines[-1].strip() == "REM file_end_sanity_check":
                    print(file_name, " is OK")
                    file.close()
                else:
                    print(file_name, " is NOT OK")
                    file.close()
                    return False  # problem occured
        except:
            return False  # problem occurred find or open a file

    return True # all files exist and read OK



def get_last_update_time():
    if not os.path.exists(LAST_UPDATE_FILE):
        # Create the last update file (without writing anything initially)
        with open(LAST_UPDATE_FILE, "w") as f:
            f.write(str(datetime.now()))
        return None

    try:
        # Read last update time from file
        with open(LAST_UPDATE_FILE, "r") as f:
            last_update_str = f.readline().strip()
            return datetime.strptime(last_update_str, "%Y-%m-%d %H:%M:%S.%f")  # Parse with millisecond precision
    except (FileNotFoundError, ValueError):
        # Handle errors: create empty file or invalid format
        print(f"Error reading last update file. Creating new file.")
        with open(LAST_UPDATE_FILE, "w") as f:
            f.write(str(datetime.now()))
        return None


def check_for_update():

    last_update_time = get_last_update_time()   # if first time, a new file with current time will be created.
                                                # No Update at first time
    if last_update_time is None:
        print("last update date file not found")
        return

    current_version_start = 0.0
    current_version_end = 0.0

    # Check if the last update was more than a day ago
    if datetime.now() - last_update_time < timedelta(days=UPDATE_INTERVAL):
    #if datetime.now() - last_update_time < timedelta(seconds=UPDATE_INTERVAL):
        print("Last update was within the last day. Skipping update check.")
        return
    try:
        with open(START_COPY_VERSION_FILE_NAME, "r") as f_start:
            try:
                current_version_start = float(f_start.readline().strip())
            except:
                current_version_start = 0.0
    except FileNotFoundError:
        current_version_start = 0.0

    try:
        with open(END_COPY_VERSION_FILE_NAME, "r") as f_end:
            try:
              current_version_end = float(f_end.readline().strip())
            except:
                current_version_end = 0.0
    except FileNotFoundError:
        current_version_end = 0.0

    # todo check if below is working @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    if current_version_end != current_version_start:
        # restore the last valid copy if worse comes to worse
        string_cmd = "cp -rf " + BACKUP_FOLDER + "/*.* " + "."
        os.system(string_cmd)

        # Update version file with latest version
        with open(START_COPY_VERSION_FILE_NAME, "w") as f:
            f.write("0.0")
        # Update version file with latest version
        with open(END_COPY_VERSION_FILE_NAME, "w") as f:
            f.write("0.0")

    check_res = True
    max_retries = RETRIES_FOR_INTERNET_FAILURE  # Set the maximum number of retries for request.get
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(repo_url + "/releases/latest")
            if response.status_code == REQUEST_HAS_SUCCEEDED:
                latest_version_tag_name = response.json()["tag_name"]  # should be a number

                # Compare versions (assuming current_version_start stores a float)
                if float(latest_version_tag_name) > current_version_start:
                    update_script(latest_version_tag_name)
                else:
                    print(f"Already on latest version: {current_version_start}")
                    exit(0)
                break  # Exit loop on successful request
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt}/{max_retries}: Error fetching update info: {e}")
            time.sleep(2 ** attempt)  # Exponential backoff between retries

    else:
        print("Failed to retrieve update information after retries.")
        sys.exit(-3)


def copy_files(source_path):
    shutil.copy2(os.path.join(source_path, "main.py"), ".")
    shutil.copy2(os.path.join(source_path, "run.bat"), ".")
    shutil.copy2(os.path.join(source_path, "VideoClipsRecord.py"), ".")
    shutil.copy2(os.path.join(source_path, "send_data_to_app_via_firebase.py"), ".")
    shutil.copy2(os.path.join(source_path, "config.txt"), ".")
    shutil.copy2(os.path.join(source_path, "consts.py"), ".")
    # shutil.copy2(os.path.join(source_path, "yolov8l.pt"), ".")
    #shutil.copy2(os.path.join(source_path, "updater.py"), ".") # todo


def update_script(latest_version):
    max_retries = RETRIES_FOR_CLONING_FAILURE  # Set the maximum number of retries for cloning
    copy_validity = False
    for attempt in range(1, max_retries + 1):
        try:
            delete_folder_safely(TMP_FOLDER)
            err = subprocess.run(["git", "clone", "--depth=1", repo_cloning_url, TMP_FOLDER], check=True).stderr

            # save a copy if worse comes to worse
            string_cmd = "cp -rf " + ". " + BACKUP_FOLDER

            print("save a copy if worse comes to worse : ", string_cmd)

            # todo rethink add thread
            try:
                os.system(string_cmd)
                print("saved a backup copy in : ", BACKUP_FOLDER)

            except:
                print("error in saving a backup copy of previous version")
                k = datetime.now()
                date_time_str = k.strftime('%H:%M:%S  %d/%m/%Y')
                Log(date_time_str, "error in saving a backup copy of previous version")
                sleep(3)
                exit(-1)

            # Update version file with latest version
            with open(START_COPY_VERSION_FILE_NAME, "w") as f:
                f.write(latest_version)

            if err is None:
                # Replace existing files with updated versions
                copy_files(TMP_FOLDER)

                check_res = check_all_files_are_valid(FILE_NAMES_TO_CHECK)
                if check_res == True:  # files from internet are OK
                    print("files updated correctly from the internet")
                    copy_validity = True
                else:
                    log_str = "problem updating from internet - retry load at try " + str(attempt)+" from " + str( max_retries + 1)
                    print(log_str)
                    k = datetime.now()
                    date_time_str = k.strftime('%H:%M:%S  %d/%m/%Y')
                    Log(date_time_str, log_str)

                    continue

                if copy_validity == True:
                    # Update version file with latest version
                    with open(END_COPY_VERSION_FILE_NAME, "w") as f:
                        f.write(latest_version)

                    # Update last update time after successful execution
                    with open(LAST_UPDATE_FILE, "w") as f:
                        f.write(str(datetime.now()))

                print("Successfully updated project from GitHub!")
                delete_folder_safely(TMP_FOLDER)
                break  # Exit loop on successful cloning

            else:
                log_str = "Error occurred in updating last version"
                print(log_str)
                k = datetime.now()
                date_time_str = k.strftime('%H:%M:%S  %d/%m/%Y')
                Log(date_time_str, log_str)


        except subprocess.CalledProcessError as e:
            print(f"Attempt {attempt}/{max_retries}: Error cloning repository: {e}")
            time.sleep(2 ** attempt)  # Exponential backoff between retries
    else:
        log_str = "Failed to clone the updated project after retries."
        print(log_str)
        k = datetime.now()
        date_time_str = k.strftime('%H:%M:%S  %d/%m/%Y')
        Log(date_time_str, log_str)

        copy_files(BACKUP_FOLDER)


def delete_folder_safely(folder_path):
    if not os.path.exists(folder_path):
        return  # no folder preventing cloning success
    try:
        if platform.system() == "Windows":
            change_permissions_recursive_windows(folder_path)  # Change permissions to writable for Windows
        else:
            change_permissions_recursive(folder_path, stat.S_IWRITE)  # Change permissions to writable for Unix
        shutil.rmtree(folder_path, ignore_errors=False)
    except PermissionError as e:
        log_str = f"error encountered: {e}"
        #print(f"error encountered: {e}")
        print(log_str)
        k = datetime.now()
        date_time_str = k.strftime('%H:%M:%S  %d/%m/%Y')
        Log(date_time_str, log_str)

    #print(f"Successfully deleted folder: {folder_path}")
    log_str = (f"Successfully deleted folder: {folder_path}")
    print(log_str)
    k = datetime.now()
    date_time_str = k.strftime('%H:%M:%S  %d/%m/%Y')
    Log(date_time_str, log_str)


def change_permissions_recursive(path, mode):
    for root, dirs, files in os.walk(path):
        for dir in dirs:
            os.chmod(os.path.join(root, dir), mode)
        for file in files:
            os.chmod(os.path.join(root, file), mode)


def change_permissions_recursive_windows(path):
    import ctypes
    file_attribute_readonly = 0x01

    def unset_readonly(file):
        attrs = ctypes.windll.kernel32.GetFileAttributesW(file)
        if attrs & file_attribute_readonly:
            ctypes.windll.kernel32.SetFileAttributesW(file, attrs & ~file_attribute_readonly)

    for root, dirs, files in os.walk(path):
        for dir in dirs:
            unset_readonly(os.path.join(root, dir))
        for file in files:
            unset_readonly(os.path.join(root, file))


if __name__ == "__main__":
    check_for_update()
    print("Updater Done")
#file_end_sanity_check
