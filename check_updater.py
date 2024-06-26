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


FILE_NAMES_TO_CHECK = {"./updater.py", "./main.py","./config.txt","./run.bat","./VideoClipsRecord.py","./VideoClipsRecord.py","./consts.py"}
'''
   shutil.copy2(os.path.join(source_path, "main.py"), ".")
    shutil.copy2(os.path.join(source_path, "run.bat"), ".")
    shutil.copy2(os.path.join(source_path, "VideoClipsRecord.py"), ".")
    shutil.copy2(os.path.join(source_path, "VideoClipsRecord.py"), ".")
    shutil.copy2(os.path.join(source_path, "config.txt"), ".")
    shutil.copy2(os.path.join(source_path, "consts.py"), ".")
    # shutil.copy2(os.path.join(source_path, "yolov8l.pt"), ".")
    #shutil.copy2(os.path.join(source_path, "updater.py"), ".") # todo

'''




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


if __name__ == "__main__":
    all_files_valid = check_all_files_are_valid(FILE_NAMES_TO_CHECK)
    if not all_files_valid == True:
        #need to download again
        print("need to download again")

