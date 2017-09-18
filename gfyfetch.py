#!/usr/bin/python3
import os, os.path, sys
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
TESTFILEID = 'MixedSplendidIndianspinyloache'
TMP_FILELIST= '/tmp/gfyfetch_filelist.txt'

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
    current_file_id = ""
    # Walk through directory
    for dName, sdName, fList in os.walk(inDIR):
        print("path:", dName, sdName, fList)
        for fileName in fList:
            #if fnmatch.fnmatch(fileName, unixpattern):
            m = re.match(repattern, fileName)
            #print("m: ", m)
            if m:
                current_file_id = parse_path_line(fileName)[2]
                #print("current_file_id:", current_file_id)
                if current_file_id not in fileIdSet: # have not seen this id before, it's not a dupe
                    fileIdSet.add(parse_path_line(fileName)[2]) # add file id to set
                    fileList.append(os.path.join(dName, fileName)) # add file path to list
                    count += 1
            else:
                print("filename", fileName, "doesn't match.")
    fileList.sort()
    print("fileList:", fileList)
    print("fileIdSet:", fileIdSet)
    print("count:", count)
    write_list_to_file(fileList)


def write_list_to_file(thelist):
    """Write generated list to file on disk"""

    with open(TMP_FILELIST, 'w') as file_handler:  # Use file to refer to the file object
        for item in thelist:
            file_handler.write("%s\n" % item) #or file_handler.write("{}\n".format(item))


def read_file_listing(file):
    """Read entire text file for cleanup"""
    #with open("/tmp/gfyfetch_filelist.txt") as file: # Use file to refer to the file object
    #     data = file.read()

    with open(file, 'r') as file_handler:
        data = file_handler.read()
        #print("data read: ", data)

        for line in data.splitlines(): #FIXME REMOVE DUPES
            print("line read is:", line)
        
        
        #TODO: read only the first line to process here! then remove it!
        #parse_path_line(line)


def parse_path_line(theline):
    """Strips unnecessary extension and path to isolate ID. Returns list of [file_noext, file_dirname, file_id]"""
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

def process_id(id):
    """Process the current filename"""
    print("process_id():", id)
    CURRENT_URL = None #= gfycat_client_fetcher(id)
    if CURRENT_URL != None:
        file_downloader(CURRENT_URL)
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
    def update_to(self, b=1, bsize=1, tsize=None):
        """
        b  : int, optional
            Number of blocks transferred so far [default: 1].
        bsize  : int, optional
            Size of each block (in tqdm units) [default: 1].
        tsize  : int, optional
            Total size (in tqdm units). If [default: None] remains unchanged.
        """
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)  # will also set self.n = b * bsize



def file_downloader(url):
    """Downloads the file at the url passed."""
    dst = TESTFILEID + ".mp4"
    # urlretrieve(url, dst)
    with TqdmUpTo(unit='B', unit_scale=True, miniters=1,
                  desc=url.split('/')[-1]) as t:  # all optional kwargs
        urllib.request.urlretrieve(url, filename=dst,
                                   reporthook=t.update_to, data=None)


def setup_download_dir():
    """Setup local directory structure for downloads"""
    cwd = os.getcwd()
    print("setup_download_dir().cwd:", cwd)

    #TODO: directory layout creation

def main():
    """main loop"""

    if len(sys.argv) != 2:
        print_usage()
    else:
        arg1 = str(sys.argv[1])

    if is_first_arg_dir(arg1):
        print("Scanning:", arg1)
        scan_directory(str(arg1))
        read_file_listing(TMP_FILELIST)
    else:
        print("Using file", arg1, "as file listing.")
        read_file_listing(str(arg1))

    setup_download_dir()
    #TODO: recap file listing in stdout and *wait for keypress*
    #TODO: then fire a while true loop with input() to break it gracefully (finish download + remove filename from text AFTER completion)

main()

#TODO: interruption handling

#TODO: error handling

#TODO: handle when mp4 already exists (rename already existing file as filename_conv.mp4?)