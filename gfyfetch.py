#!/usr/bin/python3
import os, os.path, sys
import subprocess
#import fnmatch
#import shutil
import urllib
import signal
import time
import re
import requests
from tqdm import tqdm
#import json
#from urllib import urlopen
from gfycat.client import GfycatClient
from gfycat.error import GfycatClientError
# urllib.request.URLopener.version = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36'
QUERY_ENDPOINT = 'http://gfycat.com/cajax/get/'
TMP_FILELIST = '/tmp/gfyfetch_filelist.txt'
TMP_ERRORLIST = '/tmp/gfyfetch_errorlist.txt'
CWD = os.getcwd()
request_session = requests.Session()
request_session.headers.update({'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:55.0) Gecko/20100101 Firefox/54.0'})
GLOBAL_LIST_OBJECT = []

class Main:
    def __init__(self):
        self.asked_termination = False
        self.root_user = False
        signal.signal(signal.SIGINT, self.signal_handler)

    def main(self):
        if os.geteuid() == 0:
            self.root_user = True
            print(BColors.FAIL + "Running as root messes up file ownership, not recommended." + BColors.ENDC)
            exit(0)
            import keyboard # This trick only works as root but that sucks so don't do it.
            keyboard.add_hotkey('q', self.on_triggered)

        if len(sys.argv) != 2:
            self.print_usage()
        else:
            arg1 = str(sys.argv[1])

        if SetupClass.previous_tmp_file_exists(self):
            if SetupClass.setup_prompt_resume(self):
                pass

        if SetupClass.is_first_arg_dir(self, arg1):
            SetupClass.setup_use_dir(self, arg1)
        else:
            SetupClass.setup_use_file(self, arg1)

    def print_usage(self):
        """Prints script usage"""

        print('Usage: gfyfetch [DIR|LIST]\n* change current working directory \
to the one where files will be downloaded\n\
* submit location to scan as [DIR] or a file list text file with full paths [LIST]\n\
* run the program as root to be able to pause by pressing \"q\" \
and resume later (NOT recommended!).\n\
  Otherwise, run it as normal user (recommended) and press CTRL+C to pause downloads\n\
* be aware that the file listing submitted will be emptied progressively\
and deleted once its parsing & downloads are finished!\n\
* errors will be logged in /tmp/gfyfetch_error.txt by default\n')
        exit(0)

    def signal_handler(self):
        # print('You pressed Ctrl+C!:', signal, frame)
        self.asked_termination = True
        print(BColors.OKBLUE + "User asked for termination, pausing now.\n" + BColors.ENDC)


    def on_triggered(self):
        print(BColors.OKBLUE + "Terminating!" + BColors.ENDC)
        self.asked_termination = True

    def terminate(self):
        if self.asked_termination:
            print("asked_termination was:", self.asked_termination, "terminate() bye!")
            # signal.pause()
            sys.exit(0)

    def loop_through_text_file(self, file):
        """Main iterating loop"""

        self.asked_termination = False

        while True:

            if self.asked_termination:
                break

            print("LOOP START: asked_termination is: ", self.asked_termination)

            dir_id_pair = File_Util.read_first_line(self, file) #retrieve parent_dir/file_id from text list
            SetupClass.setup_download_dir(self, dir_id_pair[0]) #create our download directory if doesn't exist FIXME add option to set manually instead of CWD

            print("GLOBAL_LIST_OBJECT before:", GLOBAL_LIST_OBJECT)
            GLOBAL_LIST_OBJECT.extend(dir_id_pair) #FIXME instead of append/extend, create the list with empty elements and change them by index
            print("GLOBAL_LIST_OBJECT after:", GLOBAL_LIST_OBJECT)

            if Downloader.process_id(self, GLOBAL_LIST_OBJECT[0], GLOBAL_LIST_OBJECT[1]):
                File_Util.remove_first_line(self, file) #TODO only remove after download succeeds
                del GLOBAL_LIST_OBJECT[:]
                time.sleep(3)
            else:
                print(BColors.FAIL + "Download of " + GLOBAL_LIST_OBJECT[0] + "/" + GLOBAL_LIST_OBJECT[1] + " failed! Reason: " + GLOBAL_LIST_OBJECT[2] + BColors.ENDC)
                File_Util.write_error_to_file(self, str(GLOBAL_LIST_OBJECT[0] + "/" + GLOBAL_LIST_OBJECT[1] + " failed! Reason: " + GLOBAL_LIST_OBJECT[2]))
                del GLOBAL_LIST_OBJECT[:]
                File_Util.remove_first_line(self, file)
                time.sleep(1)

            # signal.pause()

class BColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class List_Generator:
    def __init__(self):
        pass

    def scan_directory(self, inDIR):
        """Walks directory and scrape files according to pattern"""

        #unixpattern = '*.webm|*.gif'
        repattern = r'^([A-Z][a-z]+[^0-9\s\_\-\\\'])+(\.webm|\.gif|\.mp4)$' #TODO: option to ignore already existing mp4s
        #matches strings starting with 1 capital, 1 lowercase, no number or whitespaces
        fileList = []
        fileIdSet = set()
        count = 0
        dupecount = 0
        current_file_props = []
        # Walk through directory
        for dName, sdName, fList in os.walk(inDIR):
            #print("path:", dName, sdName, fList)
            for fileName in fList:
                #if fnmatch.fnmatch(fileName, unixpattern):
                m = re.match(repattern, fileName)
                #print("m: ", m)
                if m:
                    current_file_props = File_Util.parse_path_line(self, fileName)
                    #print("current_file_id:", current_file_id)
                    if current_file_props[2] not in fileIdSet: # not seen this id before, not a dupe
                        fileIdSet.add(File_Util.parse_path_line(self, fileName)[2]) # add file id to set
                        fileList.append(os.path.join(dName, fileName)) # add file path to list
                        count += 1
                    else:
                        dupecount += 1
                # else:
                #     print("filename", fileName, "doesn't match.")
        fileList.sort()
        # print("fileList:", fileList)
        # print("fileIdSet:", fileIdSet)
        print("dupecount:", dupecount)
        File_Util.write_list_to_file(self, fileList)


class SetupClass:
    def __init__(self):
        pass

    def is_first_arg_dir(self, arg):
        """Scans directory and generates file listing text."""

        if os.path.isdir(arg):
            return True
        elif os.path.exists(arg):
            return False
        else:
            print(BColors.WARNING + "Error:", arg + " is not a valid directory or file!" + BColors.ENDC)
            exit(1)

    def setup_download_dir(self, directory):
        """Setup local directory structure for downloads"""
        if not os.path.exists(CWD + os.sep + directory):
            os.makedirs(CWD + os.sep + directory)


    def setup_use_dir(self, directory):
        """Starts logic to scan supplied dir path"""
        print("Scanning directory:", directory)
        List_Generator.scan_directory(self, directory)
        if File_Util.read_file_listing(self, TMP_FILELIST):
            Main.loop_through_text_file(self, TMP_FILELIST)

    def setup_use_file(self, file):
        """Starts logic to use a supplied file list"""
        print("Using supplied file list '" + file + "' as file listing.")
        if File_Util.read_file_listing(self, file):
            Main.loop_through_text_file(self, file)

    def setup_prompt_resume(self):
        """Prompts user to resume from existing file in default location"""
        question = BColors.HEADER + "Warning: a previous file listing is present in " + TMP_FILELIST + "\nWould you like to load listing from it?" + BColors.ENDC
        if SetupClass.query_yes_no(self, question):
            SetupClass.setup_use_file(self, TMP_FILELIST)
            return True
        else:
            return False


    def previous_tmp_file_exists(self):
        """Checks if a previously generated file listing is in default location"""
        if os.path.exists(TMP_FILELIST):
            return True
        return False

    def query_yes_no(self, question, default="yes"):
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


class File_Util:
    def __init__(self):
        pass

    def parse_path_line(self, theline):
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

    def write_list_to_file(self, thelist):
        """Write generated list to file on disk"""

        with open(TMP_FILELIST, 'w') as file_handler:
            for item in thelist:
                file_handler.write("%s\n" % item) #file_handler.write("{}\n".format(item))


    def read_file_listing(self, file):
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
                current_file_props = File_Util.parse_path_line(self, line)
                dir_id_pair = current_file_props[1] + "/" + current_file_props[2]
                if dir_id_pair not in dir_id_pair_set: # skip if dir/fileid already been seen
                    dir_id_pair_set.add(dir_id_pair)
                    #process_id(current_file_props[1], current_file_props[2])
                    clean_list.append(line)

            File_Util.write_list_to_file(self, clean_list) #rewriting to file
            return True
            #TODO: don't call read_file_listing if scan has been done already?
        return False

    def write_error_to_file(self, item):
        """Write file IDs that generated errors to file"""
        with open(TMP_ERRORLIST, 'a') as file_handler:
            file_handler.write("%s\n" % item) #file_handler.write("{}\n".format(item))

    def read_first_line(self, file):
        """Only read the first line of file"""

        try:
            if os.stat(file).st_size == 0:
                os.remove(file)
                print("End of file listing. Exiting.")
                exit(0)
        except OSError as e:
            print("Read first line error:", e)
            exit(1)

        with open(file, 'r') as file_handler:
            firstline = file_handler.readline()
            current_file_props = File_Util.parse_path_line(self, firstline)
            return [current_file_props[1], current_file_props[2]]


    def remove_first_line(self, file):
        """Remove the first line from file"""

        cmd = ['sed', '-i', '-e', "1d", file]
        subprocess_call = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = subprocess_call.communicate()
        if err:
            raise NameError(
                '\n============= WARNING/ERROR ===============\n{}\n===========================================\n'.format(err.rstrip()))
        #return out



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

        # if int(block * blocksize * 100 / totalsize) == 100:
        #     tqdm.write(BColors.BOLD + "Download completed!" + BColors.ENDC)

class Downloader:

    def __init__(self):
        pass

    def process_id(self, download_dir, file_id):
        """Process the current filename"""

        #GLOBAL_LIST_OBJECT: [ "download_dir", "file_id", "fetched_url_mp4" ]
        if not Downloader.gfycat_client_fetcher(self, file_id):
            return False

        Downloader.generate_dest_filename(self, GLOBAL_LIST_OBJECT[0], GLOBAL_LIST_OBJECT[1])

        if GLOBAL_LIST_OBJECT[2] != None:
            if Downloader.file_downloader(self, GLOBAL_LIST_OBJECT[2]):
                return True
            else:
                return False
        else:
            return False

    def gfycat_client_fetcher(self, arg):
        """Uses the gfycat.client library to fetch JSON, returns mp4Url"""
        client = GfycatClient() #TODO: copy over gfycat.client code and spoof UA in requests

        try:
            myquery = client.query_gfy(arg) #dict
        except GfycatClientError as error:
            print(error.error_message)
            print(error.status_code)
            return False

        try:
            if 'error' in myquery: # (myquery['error']):
                print(BColors.FAIL + "JSON Fetcher Warning:", myquery['error'], BColors.ENDC)
                GLOBAL_LIST_OBJECT.append(myquery['error'])
                return False
            else:
                print(BColors.OKGREEN + "mp4Url value = ", myquery['gfyItem']['mp4Url'], BColors.ENDC)
                GLOBAL_LIST_OBJECT.append(myquery['gfyItem']['mp4Url'])
                return True
        except:
            print(BColors.FAIL + "JSON Fetcher exception error: " + ValueError + BColors.ENDC)
            return False
        return False

    # def gfycat_fetcher():
    #     """Standalone fetching of JSON, returns mp4Url"""
    #     j = urllib.request.urlopen(QUERY_ENDPOINT+TESTFILEID)
    #     j_obj = json.load(j)
    #     print("mp4Url value = ", j_obj['gfyItem']['mp4Url'])
    #     return j_obj['gfyItem']['mp4Url']

    def file_downloader2(self, url):
        """Downloads the file at the url passed."""

        # user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36'
        # myheaders = {'User-Agent': user_agent}
        dst = self.generate_dest_filename(GLOBAL_LIST_OBJECT[0], GLOBAL_LIST_OBJECT[1])

        with TqdmUpTo(unit='B', unit_scale=True, miniters=1, desc=url.split('/')[-1]) as t:  # all optional kwargs
            local_filename, headers = urllib.request.urlretrieve(url, filename=dst, reporthook=t.update_to, data=None)

        print("contentlength: ", headers['Content-Length'])
        checkfile = open(local_filename)
        if checkfile:
            tqdm.write(BColors.BOLD + "Download completed!" + BColors.ENDC)
        checkfile.close()

        if os.path.exists(local_filename):
            return True
        else:
            return False
        return False



    def file_downloader(self, url):
        """Downloads the file at the url passed."""
        dst = Downloader.generate_dest_filename(self, GLOBAL_LIST_OBJECT[0], GLOBAL_LIST_OBJECT[1])
        print("dst: ", dst)
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/536.36'}

        # url="http://httpbin.org/headers" #for testing
        chunkSize = 1024

        r = request_session.get(url, headers=headers, stream=True)
        if r.status_code != 200:
            tqdm.write(BColors.FAIL + "Error fetching the URL: " + r.status_code + BColors.ENDC)
            return False
        with open(dst, 'wb') as f:
            pbar = tqdm(unit="B", total=int(r.headers['Content-Length']))
            for chunk in r.iter_content(chunk_size=chunkSize):
                if chunk: # filter out keep-alive new chunks
                    pbar.update(len(chunk))
                    f.write(chunk)
        tqdm.write(BColors.BOLD + "\nDownload of " + GLOBAL_LIST_OBJECT[0] + "/" + GLOBAL_LIST_OBJECT[1] + " completed!" + BColors.ENDC)
        # return dst
        return True



    def generate_dest_filename(self, download_dir, file_id):
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



if __name__ == "__main__":
    main_obj = Main()
    main_obj.main()

#TODO: recap file listing in stdout and *wait for keypress*
#TODO: then fire a while true loop with input() to break it gracefully (finish download + remove filename from text AFTER completion)
#TODO: interruption handling
#TODO: error handling
