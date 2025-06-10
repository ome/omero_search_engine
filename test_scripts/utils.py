import os
import shutil

def copy_scripts_subfolder():
    """
    Copy the test_scripts folder to the test_scripts
    inside the searchengine folder
    """
    subfolder = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "../test_scripts"
    )
    destination_folder = "/etc/searchengine/"
    if not os.path.isdir(destination_folder):
        destination_folder = os.path.expanduser("~")
    destination_folder = os.path.join(destination_folder, "test_scripts")

    if not os.path.isdir(destination_folder):
        shutil.copytree(subfolder, destination_folder,ignore=shutil.ignore_patterns( '__pycache__'))

