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
    print("mainloop:", dir_id_pair)
    if process_id(dir_id_pair[0], dir_id_pair[1]):
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

    print("process_id(): download_dir file_id", download_dir, file_id)
    url_object = [] 
    #url_object[3] = gfycat_client_fetcher(file_id)
    # if url_object != None:
    #     file_downloader(url_object)
    # else:
    #     pass

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

def file_downloader(list):
    """Downloads the file at the url passed."""
    dst = list[0] + os.path + list[2] + ".mp4" #TODO replace with file_Id and download_dir here
    # urlretrieve(url, dst)
    with TqdmUpTo(unit='B', unit_scale=True, miniters=1, desc=list[3].split('/')[-1]) as t:  # all optional kwargs
        urllib.request.urlretrieve(list[3], filename=dst, reporthook=t.update_to, data=None)


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
        print("Scanning directory:", arg1)
        scan_directory(arg1)
        if read_file_listing(TMP_FILELIST):
            setup_download_dir()
            loop_through_text_file(TMP_FILELIST)
    else:
        print("Using file list", arg1, "as file listing.")
        if read_file_listing(arg1):
            setup_download_dir()
            loop_through_text_file(arg1)

    #TODO: recap file listing in stdout and *wait for keypress*
    #TODO: then fire a while true loop with input() to break it gracefully (finish download + remove filename from text AFTER completion)

main()

#TODO: interruption handling

#TODO: error handling

#TODO: handle when mp4 already exists (rename already existing file as filename_conv.mp4?)