import os
import shutil
from tempfile import gettempdir

SED_FOUND = True if os.path.exists(str(shutil.which("sed"))) else False

QUERY_ENDPOINT = 'http://gfycat.com/cajax/get/'
TMP = gettempdir()
FILELIST = 'gfyfetch_filelist.txt'
ERRORLIST = 'gfyfetch_errorlist.txt'
ORIGINAL_FILELIST = 'gfyfetch_original_file_list.txt'
ORIGINAL_FILELIST_SELECTED = 'gfyfetch_original_file_list_selected.txt'
CWD = os.getcwd()
DB_CHECKED_LIST = 'gfyfetch_dbchecks.txt'
DOWNLOAD_LIST = 'gfyfetch_downloads.txt'

# GLOBAL_LIST_OBJECT = {"parent_dir" : "", "file_id": "", \
# "remnant_size": "", "mp4Url": "", "download_size": "", "error": "", "source": ""}

RAND_MIN = 1
RAND_MAX = 2

class BColors:
    """Color codes for stdout"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    BLUEOK = OKBLUE + "[OK]: " + ENDC
