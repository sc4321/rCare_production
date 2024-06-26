#file_start_sanity_check
import time
import requests
import subprocess  # For secure updates using Git
from datetime import datetime, timedelta  # For scheduling daily checks
import os
import shutil
import stat  # Import the stat module
import platform

# GitHub repository URL
repo_url = "https://api.github.com/repos/sc4321/rCare_production"
repo_cloning_url = "https://github.com/sc4321/rCare_production.git"

# Last update file path
LAST_UPDATE_FILE = "last_updated_time.txt"
CLONED_FOLDER_PATH = "./updated_project"
TMP_FOLDER = r"c:/tmp/rCare/"
BACKUP_FOLDER = "../production_back"
START_COPY_VERSION_FILE_NAME = "version_start_copy.txt"
END_COPY_VERSION_FILE_NAME = "version_end_copy.txt"

# Update check interval (in days)
UPDATE_INTERVAL = 1

# Magic numbers:
REQUEST_HAS_SUCCEEDED = 200
RETRIES_FOR_INTERNET_FAILURE = 5
RETRIES_FOR_CLONING_FAILURE = 5


# PC restart
# def PC_restart():
#    os.system("shutdown /r /t 0")

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
    last_update_time = get_last_update_time()
    if last_update_time is None:
        return  # Handle error getting last update time

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

        exit(0)

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
                break  # Exit loop on successful request
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt}/{max_retries}: Error fetching update info: {e}")
            time.sleep(2 ** attempt)  # Exponential backoff between retries
    else:
        print("Failed to retrieve update information after retries.")


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
    for attempt in range(1, max_retries + 1):
        try:
            delete_folder_safely(TMP_FOLDER)
            err = subprocess.run(["git", "clone", "--depth=1", repo_cloning_url, TMP_FOLDER], check=True).stderr

            # save a copy if worse comes to worse

            string_cmd = "cp -rf " + ". " + BACKUP_FOLDER

            print("save a copy if worse comes to worse = ", string_cmd)

            # todo rethink add thread
            try:
                os.system(string_cmd)
            except:
                print("error in saving a backup copy of previous version")
                sleep(3)
                exit(-1)

            # Update version file with latest version
            with open(START_COPY_VERSION_FILE_NAME, "w") as f:
                f.write(latest_version)

            if err is None:
                # Replace existing files with updated versions
                copy_files(TMP_FOLDER)

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
                print("Error occoured in updating last version")

        except subprocess.CalledProcessError as e:
            print(f"Attempt {attempt}/{max_retries}: Error cloning repository: {e}")
            time.sleep(2 ** attempt)  # Exponential backoff between retries
    else:
        print("Failed to clone the updated project after retries.")
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
        print(f"error encountered: {e}")
    print(f"Successfully deleted folder: {folder_path}")


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
