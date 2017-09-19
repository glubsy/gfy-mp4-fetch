#!/usr/bin/python3
import os, os.path, sys
import subprocess
#import fnmatch
#import shutil
import urllib
#import requests
import re
from tqdm import tqdm
#import json
#from urllib import urlopen
from gfycat.client import GfycatClient
from gfycat.error import GfycatClientError
QUERY_ENDPOINT = 'http://gfycat.com/cajax/get/'
TMP_FILELIST= '/tmp/gfyfetch_filelist.txt'
GLOBAL_URL_OBJECT = []
CWD = os.getcwd()

def print_usage():
    """Prints script usage"""

    print("  Usage: gfyfetch [DIR|LIST]")
    print("* change current working directory to the one where files will be downloaded")
    print("* submit location to scan as [DIR] or a file list text file with full paths [LIST]")
    exit(1)

class BColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def is_first_arg_dir(arg):
    """Scans directory and generates file listing text."""

    if os.path.isdir(arg):
        return True
    elif os.path.exists(arg):
        return False
    else:
        print(BColors.WARNING + "Error:", arg + " is not a valid directory or file!" + BColors.ENDC)
        exit(1)


def scan_directory(inDIR):
    """Walks directory and scrape files according to pattern"""

    #unixpattern = '*.webm|*.gif'
    repattern = r'^([A-Z][a-z]+[^0-9\s\_\-\\\'])+(\.webm|\.gif|\.mp4)$' #TODO: option to ignore already existing mp4s
    #matches strings starting with 1 capital, 1 lowercase, no number or whitespaces
    fileList = []
    fileIdSet = set()
    count = 0
    current_file_props = []
    # Walk through directory
    for dName, sdName, fList in os.walk(inDIR):
        #print("path:", dName, sdName, fList)
        for fileName in fList:
            #if fnmatch.fnmatch(fileName, unixpattern):
            m = re.match(repattern, fileName)
            #print("m: ", m)
            if m:
                current_file_props = parse_path_line(fileName)
                #print("current_file_id:", current_file_id)
                if current_file_props[2] not in fileIdSet: # not seen this id before, not a dupe
                    fileIdSet.add(parse_path_line(fileName)[2]) # add file id to set
                    fileList.append(os.path.join(dName, fileName)) # add file path to list
                    count += 1
            # else:
            #     print("filename", fileName, "doesn't match.")
    fileList.sort()
    print("fileList:", fileList)
    print("fileIdSet:", fileIdSet)
    print("count:", count)
    write_list_to_file(fileList)


def write_list_to_file(thelist):
    """Write generated list to file on disk"""

    with open(TMP_FILELIST, 'w') as file_handler:
        for item in thelist:
            file_handler.write("%s\n" % item) #file_handler.write("{}\n".format(item))


def read_file_listing(file):
    """Read entire text file check for dupes"""

    current_file_props = []
    dir_id_pair = []
    dir_id_pair_set = set()
    clean_list = []

    with open(file, 'r') as file_handler:
        data = file_handler.read()
        #print("data read: ", data)

        for line in data.splitlines():
            #print("read_file_listing() read line:", line)
            current_file_props = parse_path_line(line)
            dir_id_pair = current_file_props[1] + "/" + current_file_props[2]
            if dir_id_pair not in dir_id_pair_set: # skip if dir/fileid already been seen
                dir_id_pair_set.add(dir_id_pair)
                #process_id(current_file_props[1], current_file_props[2])
                clean_list.append(line)
        
        write_list_to_file(clean_list) #rewriting to file
        return True
        #TODO: don't call read_file_listing if scan has been done already?
    return False


def loop_through_text_file(file):
    """main iterating loop"""

    dir_id_pair = read_first_line(file)
    setup_download_dir(dir_id_pair[0])

    GLOBAL_URL_OBJECT.append(dir_id_pair[0]) #download_dir #FIXME instead of append, create the list with empty elements and change them by index
    GLOBAL_URL_OBJECT.append(dir_id_pair[1]) #file_id
    if process_id(GLOBAL_URL_OBJECT[0], GLOBAL_URL_OBJECT[1]):
        remove_first_line(file) # Only remove after download succeeds TODO


def read_first_line(file):
    """Only read the first line of file"""

    with open(file, 'r') as file_handler:
        firstline = file_handler.readline()
        current_file_props = parse_path_line(firstline)
        return [current_file_props[1], current_file_props[2]]


def remove_first_line(file):
    """Remove the first line from file"""

    cmd = ['sed', '-i', '-e', "1d", file]
    subprocess_call = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = subprocess_call.communicate()
    if err:
        raise NameError(
            '\n============= WARNING/ERROR ===============\n{}\n===========================================\n'.format(err.rstrip()))
    return out


def parse_path_line(theline):
    """Strips unnecessary extension and path to isolate ID.
       Returns list of [file_noext, file_dirname, file_id]"""

    # filepath_noext = os.path.split(os.path.splitext(theline)[0])
    file_noext = os.path.splitext(theline)[0]
    file_dirname = os.path.basename(os.path.dirname(theline))
    file_id = os.path.basename(file_noext)
    file_props = [file_noext, file_dirname, file_id]
    # print("file_noext:", file_noext)
    # print("file_dirname:", file_dirname)
    # print("file_id:", file_id)
    return file_props
    #process_id(file_id)

def process_id(download_dir, file_id):
    """Process the current filename"""

    print("process_id() download_dir:", download_dir, "file_id:", file_id)
    #GLOBAL_URL_OBJECT: [ "download_dir", "file_id", "fetched_url_mp4" ]
    GLOBAL_URL_OBJECT.append(gfycat_client_fetcher(file_id))

    generate_dest_filename(GLOBAL_URL_OBJECT[0], GLOBAL_URL_OBJECT[1])

    if GLOBAL_URL_OBJECT[2] != None:
        file_downloader(GLOBAL_URL_OBJECT[2])
    else:
        pass

def gfycat_client_fetcher(arg):
    """Uses the gfycat.client library to fetch JSON, returns mp4Url"""
    client = GfycatClient()

    try:
        myquery = client.query_gfy(arg) #dict
    except GfycatClientError as error:
        print(error.error_message)
        print(error.status_code)

    try:
        if 'error' in myquery: # (myquery['error']):
            print(BColors.FAIL + "WARNING:", myquery['error'], BColors.ENDC)
        else:
            print(BColors.OKGREEN + "mp4Url value = ", myquery['gfyItem']['mp4Url'], BColors.ENDC)
            return myquery['gfyItem']['mp4Url']
    except:
        print(BColors.FAIL + "There was an error: ", ValueError)

# def new_json_parser():
#     """Standalone fetching of JSON, returns mp4Url"""
#     j = urllib.request.urlopen(QUERY_ENDPOINT+TESTFILEID)
#     j_obj = json.load(j)
#     print("mp4Url value = ", j_obj['gfyItem']['mp4Url'])
#     return j_obj['gfyItem']['mp4Url']

class TqdmUpTo(tqdm):
    """Provides `update_to(n)` which uses `tqdm.update(delta_n)`."""
    def update_to(self, block=1, blocksize=1, totalsize=None):
        """
        b  : int, optional
            Number of blocks transferred so far [default: 1].
        bsize  : int, optional
            Size of each block (in tqdm units) [default: 1].
        tsize  : int, optional
            Total size (in tqdm units). If [default: None] remains unchanged.
        """
        if totalsize is not None:
            self.total = totalsize
        self.update(block * blocksize - self.n)  # will also set self.n = b * bsize

        if int(block * blocksize * 100 / totalsize) == 100:
            print(BColors.BOLD + "Download completed!" + BColors.ENDC) #FIXME: what if no totalsize?



def file_downloader(url):
    """Downloads the file at the url passed."""

    dst = generate_dest_filename(GLOBAL_URL_OBJECT[0], GLOBAL_URL_OBJECT[1])
    print("dest: ", dst)
    with TqdmUpTo(unit='B', unit_scale=True, miniters=1, desc=url.split('/')[-1]) as t:  # all optional kwargs
        urllib.request.urlretrieve(url, filename=dst, reporthook=t.update_to, data=None)



def generate_dest_filename(download_dir, file_id):
    """make final filename for file to be written"""
    try_number = 1
    download_dest = CWD + os.sep + download_dir + os.sep + file_id + ".mp4"

    while os.path.exists(download_dest):
        download_dest = CWD + os.sep + download_dir + os.sep + file_id + ("_(%s)" %(try_number)) + ".mp4"
        try_number += 1
        if not os.path.exists(download_dest): 
            # We have finally found an unused filename, we keep it
            break
    return download_dest


def setup_download_dir(dir):
    """Setup local directory structure for downloads"""
    if not os.path.exists(CWD + os.sep + dir):
        os.makedirs(CWD + os.sep + dir)


def setup_use_dir(dir):
    """Starts logic to scan supplied dir path"""
    print("Scanning directory:", dir)
    scan_directory(dir)
    if read_file_listing(TMP_FILELIST):
        loop_through_text_file(TMP_FILELIST)

def setup_use_file(file):
    """Starts logic to use a supplied file list"""
    print("Using file list", file, "as file listing.")
    if read_file_listing(file):
        loop_through_text_file(file)

def setup_prompt_resume():
    """Prompts user to resume from existing file in default location"""
    question = BColors.HEADER + "Warning: a previous file listing is present in " + TMP_FILELIST + "\nWould you like to load listing from it?" + BColors.ENDC
    if query_yes_no(question):
        setup_use_file(TMP_FILELIST)
    else:
        pass

def previous_tmp_file_exists():
    """Checks if a previously generated file listing is in default location"""
    if os.path.exists(TMP_FILELIST):
        return True
    return False

def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.
    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")


def main():
    """init"""

    if len(sys.argv) != 2:
        print_usage()
    else:
        arg1 = str(sys.argv[1])

    if previous_tmp_file_exists():
        setup_prompt_resume()

    if is_first_arg_dir(arg1):
        setup_use_dir(arg1)
    else:
        setup_use_file(arg1)

main()

#TODO: recap file listing in stdout and *wait for keypress*
#TODO: then fire a while true loop with input() to break it gracefully (finish download + remove filename from text AFTER completion)
#TODO: interruption handling
#TODO: error handling
