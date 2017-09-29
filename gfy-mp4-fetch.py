#!/usr/bin/python3
"""Fetches corresponding mp4 for gfycat webm/gif files found on disk"""
import os
import sys
import subprocess
# import fnmatch
import argparse
import shutil
#import urllib
import signal
import time
import re
# import tty
# import termios
import random
from tempfile import gettempdir
import requests
# import _thread

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
#import json

SED_FOUND = True if os.path.exists(str(shutil.which("sed"))) else False

QUERY_ENDPOINT = 'http://gfycat.com/cajax/get/'
TMP = gettempdir()
FILELIST = 'gfyfetch_filelist.txt'
ERRORLIST = 'gfyfetch_errorlist.txt'
ORIGINAL_FILELIST = 'gfyfetch_original_file_list.txt'
ORIGINAL_FILELIST_SELECTED = 'gfyfetch_original_file_list_selected.txt'
CWD = os.getcwd()

GLOBAL_LIST_OBJECT = {"parent_dir" : "", "file_id": "", \
"remnant_size": "", "mp4Url": "", "download_size": "", "error": ""}

RAND_MIN = 1


class Main():
    """Main"""

    def __init__(self):
        self.asked_termination = False
        self.root_user = False
        signal.signal(signal.SIGINT, self.signal_handler) #handle pressing ctrl+c on Linux
        self.break_now = False
        self.sigint_again = False
        self.has_text_listing_been_generated = False
        self.id_set = set()
        self.input_dirorlist = ""
        self.outputdir = ""
        self.filelist = ""
        self.errorlist = ""
        self.original_filelist = ""
        self.original_filelistselected = ""
        self.maxseconds = int()
        self.diff_program = ""
        self.original_longest_line = ""

    def main(self):
        """This is wrong"""

        if os.geteuid() == 0:
            self.root_user = True
            print(BColors.FAIL + "Running as root messes up file ownership, \
not recommended." + BColors.ENDC)
            exit(0)
            import keyboard # This trick only works as root, not good
            keyboard.add_hotkey('q', self.on_triggered)


        argparser = argparse.ArgumentParser(description=\
        "Crawls a specified directory for gfycat webm/gif and downloads their mp4 equivalents.\n\
        Use ctrl+c once to pause after a download is done, twice to force quit.\n\
        Errors will be logged in /tmp/gfyfetch_error.txt by default")

        group = argparser.add_mutually_exclusive_group()

        argparser.add_argument("input", type=str, metavar="INPUT", help=\
        "input directory to scan or file list txt to parse")
        argparser.add_argument("-o", "--outputdir", dest="outputdir", type=str, metavar="path", help=\
        "target directory for downloads (default is current working dir)", default=CWD)
        argparser.add_argument("-l", "--filelist", dest="filelist", type=str, metavar="path", help=\
        "path to generate file listing into (default is TEMP)", default=TMP)
        argparser.add_argument("-e", "--errorlist", dest="errorlist", metavar="path", type=str, help=\
        "path to generate file listing into (default is $cwd)", default=CWD)
        argparser.add_argument("-s", "--seconds", dest="maxseconds", type=int, metavar="seconds", help=\
        "maximum number of seconds to wait before next download (default is 7)", default=7)
        group.add_argument("-d", "--diff", dest="diff", type=str, help=\
        "program to use for diplaying differences between original list \
and retained files by regexp (default diffmerge, falls back to diff on Linux)", \
        metavar=("program", "args"), nargs="+", default=("diffmerge", ""))
        group.add_argument("--nodiff", dest="nodiff", action='store_true', help=\
        "disable regex scrape difference checks with diff after directory scan", default=False)

        args = argparser.parse_args()
        diffargs = vars(args)

        MAIN_OBJ.input_dirorlist = args.input
        MAIN_OBJ.outputdir = str(args.outputdir).rstrip("/") + os.sep
        MAIN_OBJ.filelist = args.filelist + os.sep + FILELIST
        MAIN_OBJ.errorlist = str(args.errorlist).rstrip("/") + os.sep + ERRORLIST
        MAIN_OBJ.original_filelist = TMP + os.sep + ORIGINAL_FILELIST
        MAIN_OBJ.original_filelistselected = TMP + os.sep + ORIGINAL_FILELIST_SELECTED
        MAIN_OBJ.maxseconds = args.maxseconds

        if args.nodiff:
            MAIN_OBJ.diff_program = None
        else:
            #isolating diff program supplied
            MAIN_OBJ.diff_program = (str(diffargs["diff"][0]).split())
            # MAIN_OBJ.diff_program = args.diff[0]

        #TODO: add extension to filter (only webm, only mp4, only gif, all)

        # print("ARGUMENTS:", "\ninput_dirorlist", MAIN_OBJ.outputdir, "\noutputdir", \
        # MAIN_OBJ.outputdir, "\nfilelist", MAIN_OBJ.filelist, "\nerrorlist", MAIN_OBJ.errorlist,\
        # "\noriginal_filelist", MAIN_OBJ.original_filelist, \
        # "\noriginal_filelistselected", MAIN_OBJ.original_filelistselected)

        if SetupClass.previous_tmp_file_exists(self):
            if not SetupClass.setup_prompt_resume(self):
                if SetupClass.is_first_arg_dir(self, self.input_dirorlist):
                    SetupClass.setup_use_dir(self, self.input_dirorlist)
                else:
                    SetupClass.setup_use_file(self, self.input_dirorlist)
        else:
            if SetupClass.is_first_arg_dir(self, self.input_dirorlist):
                SetupClass.setup_use_dir(self, self.input_dirorlist)
            else:
                SetupClass.setup_use_file(self, self.input_dirorlist)


    def is_sigint_called_twice(self):
        """Check if pressing ctrl+c a second time to terminate immediately"""
        if not self.sigint_again:
            self.sigint_again = True
            return False
        FileUtil.write_string_to_file(self, str("Script has been forcefully terminated"), MAIN_OBJ.errorlist)
        return True


    def signal_handler(self, sig, frame):
        """Handles SIGINT signal, blocks it to terminate gracefully
        after the current download has finished"""
        # print('You pressed Ctrl+C!:', signal, frame)
        if self.is_sigint_called_twice():
            print("\nTerminating script!")
            sys.exit(0)

        self.asked_termination = True
        print(BColors.OKBLUE + "\nUser asked for soft termination, pausing soon.\n" + BColors.ENDC)


    def on_triggered(self):
        """If using keyboard module, pressed q as root"""
        print(BColors.OKBLUE + "Terminating!" + BColors.ENDC)
        self.asked_termination = True


    def terminate(self):
        """Forced termination"""
        if self.asked_termination:
            print(BColors.FAIL + "Forced terminating script. \
Watch out for partially downloaded files!" + BColors.ENDC)
            # signal.pause()
            sys.exit(0)


    def entry_point(self, file):
        """Final check before loop"""

        self.asked_termination = False
        self.sigint_again = False #in case we changed it too early
        # _thread.start_new_thread(self.waitForKeyPress, ()) #thread capturing keypresses, not work

        if MAIN_OBJ.has_text_listing_been_generated:
            FileUtil.compare_lists_content(self, \
            MAIN_OBJ.original_filelist, MAIN_OBJ.original_filelistselected)

        if SetupClass.query_yes_no(self, \
        "Would you like to edit the download queue?", default="no"):
            FileUtil.display_list_content(self, file)

        if SetupClass.query_yes_no(self, \
        "We will now start downloading from the top of the queue."):
            self.loop_through_text_file(file)
        else:
            exit(0)


    def loop_through_text_file(self, file):
        """Main iterating loop"""

        while True: #FIXME do while lines still left in txt list file instead
        # while self.break_now is False:

            if self.asked_termination:
                break

            # Retrieve parent_dir/file_id from text list
            GLOBAL_LIST_OBJECT['parent_dir'], GLOBAL_LIST_OBJECT['file_id'], \
            GLOBAL_LIST_OBJECT['remnant_size'] = FileUtil.read_first_line(self, file)

            print("\n====================================================================\n"+\
            "Processing: " + GLOBAL_LIST_OBJECT['parent_dir'] + "/" + GLOBAL_LIST_OBJECT['file_id'] + "\n")

            if FileUtil.has_id_already_downloaded(self, GLOBAL_LIST_OBJECT['file_id']):
                print(BColors.OKBLUE + "Warning: the ID '" + GLOBAL_LIST_OBJECT['file_id'] + \
                "' has already been downloaded before (other directory).\n" + BColors.ENDC)

            # print(BColors.OKGREEN + "DEBUG: GLOBAL_OBJECT_LIST:", \
            # str(GLOBAL_LIST_OBJECT) + BColors.ENDC)

            if Downloader.process_id(self, GLOBAL_LIST_OBJECT['parent_dir'], \
            GLOBAL_LIST_OBJECT['file_id'], GLOBAL_LIST_OBJECT['remnant_size']):
                FileUtil.add_id_to_downloaded_set(self, GLOBAL_LIST_OBJECT['file_id'])
                FileUtil.remove_first_line(self, file)
                GLOBAL_LIST_OBJECT['error'] = None
                GLOBAL_LIST_OBJECT['remnant_size'] = None
                GLOBAL_LIST_OBJECT['download_size'] = None
                time.sleep(random.uniform(RAND_MIN, MAIN_OBJ.maxseconds))
            else:
                print(BColors.FAIL + "Download of " + GLOBAL_LIST_OBJECT['parent_dir'] + "/" + \
                GLOBAL_LIST_OBJECT['file_id'] + " failed! Reason: " + \
                GLOBAL_LIST_OBJECT['error'] + BColors.ENDC)
                FileUtil.write_error_to_file(self, MAIN_OBJ.errorlist)

                GLOBAL_LIST_OBJECT['error'] = None
                GLOBAL_LIST_OBJECT['remnant_size'] = None
                GLOBAL_LIST_OBJECT['download_size'] = None
                FileUtil.remove_first_line(self, file)
                time.sleep(random.uniform(RAND_MIN, 2))

            # signal.pause()
        return

    # Testing with thread, but not working well.
    # def getch(self):
    #     """Get key press in terminal""" #Only works in actual terminal emulators?

    #     fd = sys.stdin.fileno()
    #     old_settings = termios.tcgetattr(fd)

    #     try:
    #         tty.setraw(sys.stdin.fileno())
    #         ch = sys.stdin.read(1)
    #     finally:
    #         termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    #     return ch

    # def waitForKeyPress(self):
    #     """Catches 'q' key press and changes bool"""
    #     while True:
    #         ch = self.getch()

    #         if ch == "q": # Or skip this check and just break
    #             self.break_now = True
    #             break


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

class SetupClass:
    """Setting up various things before main loop"""

    def __init__(self):
        pass

    def is_first_arg_dir(self, arg):
        """Checks if first argument is a directory."""

        if os.path.isdir(arg):
            return True
        elif os.path.isfile(arg):
            return False
        else:
            print(BColors.WARNING + "Error:", arg + \
            " is not a valid directory or file!" + BColors.ENDC)
            exit(1)


    def setup_download_dir(self, directory):
        """Setup local directory structure for downloads"""
        if not os.path.isdir(MAIN_OBJ.outputdir + os.sep + directory):
            os.makedirs(MAIN_OBJ.outputdir + os.sep + directory)


    def setup_use_dir(self, directory):
        """Starts logic to scan supplied dir path"""
        print("Scanning directory:", directory)
        FileUtil.scan_directory(self, directory)
        if FileUtil.rewrite_file_listing(self, MAIN_OBJ.filelist):
            Main.entry_point(self, MAIN_OBJ.filelist)
        exit(0)


    def setup_use_file(self, file):
        """Starts logic to use a supplied file list"""
        print("Using supplied file list '" + file + "' as file listing.")

        if not MAIN_OBJ.has_text_listing_been_generated:
            #only checking input file in case it's not the usual name
            if FILELIST not in file:
                if not FileUtil.rewrite_file_listing(self, file):
                    print(BColors.FAIL + "ERROR parsing the file listing supplied" + BColors.ENDC)
                    exit(1)
        Main.entry_point(self, file)
        exit(0)


    def setup_prompt_resume(self):
        """Prompts user to resume from existing file in default location
        returns False if answered no"""
        question = BColors.HEADER + "Warning: a previous file listing is present in " \
        + MAIN_OBJ.filelist + "\nWould you like to load listing from it?" + BColors.ENDC
        if SetupClass.query_yes_no(self, question):
            SetupClass.setup_use_file(self, MAIN_OBJ.filelist)
        return False


    def previous_tmp_file_exists(self):
        """Checks if a previously generated file listing is in default location"""
        if os.path.isfile(MAIN_OBJ.filelist):
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


class FileUtil:
    """Various file operations"""
    def __init__(self):
        pass

    def scan_directory(self, innput_DIR):
        """Walks directory and scrape files according to pattern that
        matches strings starting with 1 capital, 1 lowercase, no number or whitespaces"""
        #we don't consider dupes if same filenames in different directories
        # unixpattern = '*.mp4'
        repattern = r'^([A-Z]+[a-z]+[A-Z]+[a-z]+[A-Z]+[a-z]+[^0-9\s\_\-\\\'])+(\.webm|\.gif|\.mp4)$'
        file_list = []
        file_id_set = set() #just to check for already seen (dupes)
        count = 0
        dupecount = 0
        current_file_props = []
        original_file_listing = []
        original_file_listing_selected = []
        # Walk through directory
        for dName, sdName, fList in os.walk(innput_DIR):
            #print("path:", dName, sdName, fList)
            for fileName in fList:
                current_filepath = os.path.join(dName, fileName)
                original_file_listing.append(current_filepath)
                #if fnmatch.fnmatch(fileName, unixpattern):
                matches = re.match(repattern, fileName)
                #print("matches: ", matches)
                if matches:
                    original_file_listing_selected.append(current_filepath)
                    current_file_props = FileUtil.parse_path_line(self, current_filepath)
                    current_pardir_filename = current_file_props[1] + os.sep + current_file_props[2]
                    #print("current_file_id:", current_file_id)
                    if current_pardir_filename not in file_id_set: # not seen this id before, no dupe
                        file_id_set.add(current_pardir_filename) # file ID + pardir
                        file_list.append(current_filepath) # add file path to list
                        if ".mp4" in fileName:
                            mp4size = str(os.path.getsize(current_filepath))
                            for index, item in enumerate(file_list):
                                if dName + os.sep + current_file_props[2] in item:
                                    newitem = item + "\t" + mp4size
                                    file_list[index] = newitem #appending file size 
                        count += 1
                    else:
                        if ".mp4" in fileName:
                            mp4size = str(os.path.getsize(current_filepath))
                            for index, item in enumerate(file_list):
                                if dName + os.sep + current_file_props[2] in item:
                                    newitem = item + "\t" + mp4size
                                    file_list[index] = newitem #appending to check against later and avoid redownloading if same
                            # print(BColors.OKBLUE + "\nfile_list:\n" + str(file_list) + BColors.ENDC)
                        dupecount += 1
                else:
                    original_file_listing_selected.append("\n")
        file_list.sort()
        original_file_listing.sort()
        original_file_listing_selected.sort()

        print("Number of duplicate IDs found:", dupecount, \
        "files. Total:", count, "files retained.")

        FileUtil.write_list_to_file(self, MAIN_OBJ.filelist, file_list)
        FileUtil.write_list_to_file(self, MAIN_OBJ.original_filelist, original_file_listing)
        FileUtil.write_list_to_file(self, MAIN_OBJ.original_filelistselected, \
        original_file_listing_selected)

        #max line length for formatting diff output in case we'll use it
        MAIN_OBJ.original_longest_line = str(len(max(original_file_listing, key=len)) * 2 + 7)
        MAIN_OBJ.has_text_listing_been_generated = True

    def parse_path_line(self, theline, wantsplits=True):
        """Strips unnecessary extension and path to isolate ID.
        Returns list of [file_noext, file_dirname, file_id, file_size]
        file_size returned only if splits=True"""

        # filepath_noext = os.path.split(os.path.splitext(theline)[0])
        file_noext = os.path.splitext(theline)[0]
        file_dirname = os.path.basename(os.path.dirname(theline))
        file_id = os.path.basename(file_noext)
        if wantsplits:
            numsplits = 0
            for splits in theline.split("\t"):
                if splits is not "":
                    numsplits += 1
                    if numsplits is 2:
                        file_size = splits.rstrip("\n")
                        # print("file_noext:", file_noext, "file_dirname:", file_dirname, "file_id", file_id, BColors.OKGREEN, "file_size:", file_size, BColors.ENDC)
                        return [file_noext, file_dirname, file_id, file_size]
        # print("file_noext:", file_noext, "file_dirname:", file_dirname, "file_id", file_id, BColors.ENDC)
        return [file_noext, file_dirname, file_id, None]


    def write_list_to_file(self, filepath, thelist):
        """Write thelist to filepath on disk
        returns True if success, False if error"""

        with open(filepath, 'w') as file_handler:
            for item in thelist:
                file_handler.write("%s\n" % item) #file_handler.write("{}\n".format(item))
        return True


    def check_file_type(self, file):
        """Uses /usr/bin/file on Linux to check file type
        returns True if ASCII text, False otherwise
        if exists=False, don't check if path already exists (for writing)"""

        if not os.path.isfile(file):
            print(BColors.FAIL + \
            "Error checking file listing content. File not found."\
            + BColors.ENDC)
            return False

        if 'linux' not in str.lower(sys.platform):
            if '.txt' not in file or not os.path.isfile(file):
                print('Error: file supplied does not end with \".txt\". Aborting.')
                return False
            else:
                return True #good enough

        cmd = ['file', file]
        subprocess_call = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE)
        out, err = subprocess_call.communicate()
        if 'ASCII text' in str(out):
            return True
        if err:
            raise NameError("Error checking file content:{}".format(err.rstrip()))
        print(BColors.FAIL + \
            "Error checking file listing content. Make sure it's an ASCII text."\
            + BColors.ENDC)
        return False


    def rewrite_file_listing(self, file):
        """Read entire text file check for duplicates
        and rewrite it (like uniq, ignoring extensions)
        in case this one list was not generated by us before
        return False if file is not valid ASCII text
        return True when file overwritten"""

        current_file_props = []
        dir_id_pair = []
        dir_id_pair_set = set()
        clean_list = []

        if not FileUtil.check_file_type(self, file):
            return False

        with open(file, 'r') as file_handler:
            data = file_handler.read()
            #print("data read: ", data)

            for line in data.splitlines():
                current_file_props = FileUtil.parse_path_line(self, line, False)
                dir_id_pair = current_file_props[1] + "/" + current_file_props[2]
                if dir_id_pair not in dir_id_pair_set: # skip if dir/fileid already been seen
                    dir_id_pair_set.add(dir_id_pair)
                    clean_list.append(line)

            clean_list.sort()
            FileUtil.write_list_to_file(self, file, clean_list) #rewriting to file
        return True


    def has_id_already_downloaded(self, fileid):
        """Keep track of already seen IDs
        return true if so"""
        if fileid not in MAIN_OBJ.id_set:
            return False
        return True


    def add_id_to_downloaded_set(self, fileid):
        """Append ID to the set to keep track of
        successful downloads"""
        if fileid not in MAIN_OBJ.id_set:
            MAIN_OBJ.id_set.add(fileid)
            return False
        return True


    def write_string_to_file(self, string, file):
        """Write string to file"""

        with open(file, 'a') as file_handler:
            file_handler.write("%s\n" % string)
            #file_handler.write("{}\n".format(item))


    def write_error_to_file(self, file):
        """Write file IDs that generated errors to file"""

        with open(file, 'a') as file_handler:
            file_handler.write("%s\n" % str(GLOBAL_LIST_OBJECT['parent_dir'] + "/" \
                + GLOBAL_LIST_OBJECT['file_id'] + " failed! Reason: " \
                + GLOBAL_LIST_OBJECT['error']))
            #file_handler.write("{}\n".format(item))


    def read_first_line(self, file):
        """Returns tuple ['parent_dir', 'file_id', 'remnant_size' ]
        or ['parent_dir', 'file_id', None ] if no remnant_size found in text list"""

        try:
            if os.stat(file).st_size == 0:
                os.remove(file)
                print("End of file listing. Exiting.")
                exit(0)
        except OSError as err:
            print("Read first line error:", err)
            exit(1)

        with open(file, 'r') as file_handler:
            return FileUtil.parse_path_line(self, file_handler.readline(), True)[1:]


    def remove_first_line(self, file):
        """Remove the first line from file.
        First, check if sed exists on the PATH
        or remove first line ourselves manually"""

        if not SED_FOUND:
            with open(file, 'r') as file_handler_in:
                data = file_handler_in.read().splitlines(True)
            with open(file, 'w') as file_handler_out:
                file_handler_out.writelines(data[1:])
        else:
            cmd = ['sed', '-i', '-e', '1d', file]
            subprocess_call = subprocess.Popen(cmd, shell=False, \
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = subprocess_call.communicate()
            if err:
                raise NameError(
                    '\n============= WARNING/ERROR ===============\n{}\n\
    ===========================================\n'.format(err.rstrip()))
            #return out


    def display_list_content(self, file):
        """Print content of file list as a recap
        in either a text editor or in stdout"""

        found_editor = os.environ.get('EDITOR', 'vim') # vim by default
        text_viewers = ['subl3', 'vi' 'nano', 'gedit', 'less', 'more', 'cat']

        if not os.path.exists(str(shutil.which(found_editor))):
            for item in text_viewers:
                if os.path.exists(str(shutil.which(item))):
                    found_editor = item
                    break

        with open(file, 'r') as file_handler:
            return True if subprocess.call([found_editor, file_handler.name]) else False

        return False #something went wrong?


    def compare_lists_content(self, original_list, original_list_filtered):
        """Fire our favourite diff tool and check differences\
        between original file layout, and the same layout with ignored files
        replaced by new lines. Just to make sure the RE worked alright"""

        if MAIN_OBJ.diff_program is None:
            #--nodiff was set
            return

        command_str = ""
        for elem in MAIN_OBJ.diff_program:
            command_str += elem
            command_str += " "

        command_list = list()
        for elem in MAIN_OBJ.diff_program:
            command_list.append(elem)

        string_diff_explanation = BColors.OKGREEN + "These are the lines we think are from gfycat.\n\
In red are the lines totally ignored, white are the ones we cared about and kept.\n\
We will ignore duplicate IDs automatically from now on.\n" + BColors.ENDC + "Opening: " +\
command_str + original_list + " " + original_list_filtered + BColors.ENDC

        if "diffmerge" in command_list[0] and os.path.exists(str(shutil.which(command_list[0]))):
            print(string_diff_explanation)
            print("diffmerge may take a little while to parse... \n")

            command_list.append(original_list)
            command_list.append(original_list_filtered)
            subprocess.run(command_list, \
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return

        elif "diffmerge" in command_list[0] and not os.path.exists(str(shutil.which(command_list[0]))):
            print(string_diff_explanation)
            if os.path.exists(str(shutil.which('diff'))):
                try:
                    subprocess.run(['diff', '--color=auto', '--left-column', \
                '-ByW', MAIN_OBJ.original_longest_line, original_list, original_list_filtered])
                    return
                except:
                    pass
            else:
                pass

        elif command_list[0] == "diff" and os.path.exists(str(shutil.which(command_list[0]))):
            print(string_diff_explanation)

            command_list.append('--color=auto')
            command_list.append('--left-column')
            command_list.append('-ByW')
            command_list.append(MAIN_OBJ.original_longest_line)
            command_list.append(original_list)
            command_list.append(original_list_filtered)
            try:
                subprocess.run(command_list)
                return
            except:
                pass

        elif os.path.exists(str(shutil.which(command_list[0]))):
            command_list.append(original_list)
            command_list.append(original_list_filtered)
            try:
                subprocess.run(command_list)
                return
            except:
                pass
        else:
            command_list[0] = "diff"
            command_list.append('--color=auto')
            command_list.append('--left-column')
            command_list.append('-ByW')
            command_list.append(MAIN_OBJ.original_longest_line)
            command_list.append(original_list)
            command_list.append(original_list_filtered)
            try:
                subprocess.run(command_list)
                return
            except:
                pass

        print(BColors.FAIL + "Failed to load diff program: " + command_list[0] + BColors.ENDC)


    def check_dupe_size(self, presentfilepath, size):
        """Return True if remnantfilepath is valid
        and the file size is the same as size"""
        if os.path.isfile(presentfilepath):
            if int(os.path.getsize(presentfilepath)) == int(size):
                return True
        return False


    def check_remnant_size(self, downloadsize, remnantsize):
        """Return True if remnant file size is the same as
        the size of the file to be downloaded"""
        if remnantsize is None:
            return False
        if remnantsize == downloadsize:
            return True
        return False


class Downloader:
    """Handles actual requests and downloading"""
    def __init__(self):
        pass

    def process_id(self, download_dir, file_id, remnantsize=None):
        """Process the current file_id to download
        in the download_dir, compare size of remnantsize with
        file about to be downloaded, skip if similar"""

        if Downloader.json_query_errored(self, Downloader.gfycat_client_fetcher(self, file_id)):
            return False

        destination = Downloader.generate_dest_filename(self, \
        GLOBAL_LIST_OBJECT['parent_dir'], GLOBAL_LIST_OBJECT['file_id'])

        if FileUtil.check_dupe_size(self, \
        str(MAIN_OBJ.outputdir + os.sep + download_dir + os.sep + file_id + ".mp4"), \
        GLOBAL_LIST_OBJECT['download_size']):
            print(BColors.WARNING + "Warning: the file about to be downloaded: " + destination + \
            " already exists (same sizes). Skipping." + BColors.ENDC)
            return True #skipping download

        if FileUtil.check_remnant_size(self, \
        GLOBAL_LIST_OBJECT['download_size'], GLOBAL_LIST_OBJECT['remnant_size']):
            print(BColors.WARNING + "Warning: the file about to be downloaded:\n" + destination + \
            "\nhas the same size of " + remnantsize + \
            " bytes as the older similar file within the same path. Skipping." + BColors.ENDC)
            return True #skipping download

        if "http" not in GLOBAL_LIST_OBJECT['mp4Url']:
            print(BColors.FAIL + "ERROR: no http in:" + GLOBAL_LIST_OBJECT['mp4Url'] + BColors.ENDC)
            return False

        # Create our download directory if doesn't exist
        SetupClass.setup_download_dir(self, GLOBAL_LIST_OBJECT['parent_dir'])

        if Downloader.file_downloader(self, GLOBAL_LIST_OBJECT['mp4Url'], destination):
            dest_filesize = os.path.getsize(destination)
            if int(GLOBAL_LIST_OBJECT['download_size']) == dest_filesize:
                return True
            else:
                print(BColors.FAIL + "Warning: downloaded file size is not the same as expected size: " + \
                GLOBAL_LIST_OBJECT['download_size'] + " != " + str(dest_filesize) + BColors.ENDC)

                GLOBAL_LIST_OBJECT['error'] = str("Expected dowload size of " + \
                str(GLOBAL_LIST_OBJECT['download_size']) + " is not the downloaded file size of " + str(dest_filesize) + "!")

        return False


    def gfycat_client_fetcher(self, arg):
        """Fetches cajax JSON from gfycat,
        returns False on any error, True on success (ie. found)"""
        client = GfycatClient()

        try:
            myquery = client.query_gfy(arg) #dict
        except GfycatClientError as error:
            print(error.error_message)
            print(error.status_code)
            return
        return myquery


    def json_query_errored(self, myquery):
        """Checks the result of the json query,
        returns True if error found, False if not
        and appends to that stupid global GLOBAL_LIST_OBJECT dict"""

        try:
            if 'error' in myquery:
                # print(BColors.FAIL + "JSON Fetcher Warning:", myquery['error'], BColors.ENDC)
                GLOBAL_LIST_OBJECT['error'] = myquery['error']
                return True

            print(BColors.OKGREEN + "MP4 URL is:", \
            myquery['gfyItem']['mp4Url'], "and its size is:", myquery['gfyItem']['mp4Size'], BColors.ENDC)

            GLOBAL_LIST_OBJECT['mp4Url'] = myquery['gfyItem']['mp4Url']
            GLOBAL_LIST_OBJECT['download_size'] = myquery['gfyItem']['mp4Size']
            return False
        except:
            print(BColors.FAIL + "JSON Fetcher exception error: " + ValueError + BColors.ENDC)
            return True
        return True


    # def gfycat_fetcher(self, url):
    #     """Standalone fetching of JSON, returns mp4Url"""
    #     j = urllib.request.urlopen(url)
    #     j_obj = json.load(j)
    #     print("mp4Url value = ", j_obj['gfyItem']['mp4Url'])
    #     return j_obj['gfyItem']['mp4Url']

# if TQDM_AVAILABLE:
#     class TqdmUpTo(tqdm):
#         """Provides `update_to(n)` which uses `tqdm.update(delta_n)`."""
#         def update_to(self, block=1, blocksize=1, totalsize=None):
#             """
#             b  : int, optional
#                 Number of blocks transferred so far [default: 1].
#             bsize  : int, optional
#                 Size of each block (in tqdm units) [default: 1].
#             tsize  : int, optional
#                 Total size (in tqdm units). If [default: None] remains unchanged.
#             """
#             if totalsize is not None:
#                 self.total = totalsize
#             self.update(block * blocksize - self.n)  # will also set self.n = b * bsize

#             # if int(block * blocksize * 100 / totalsize) == 100:
#             #     tqdm.write(BColors.BOLD + "Download completed!" + BColors.ENDC)

    # def file_downloader2(self, url): #now obsolete
    #     """Downloads the file at the url passed."""

    #     dst = self.generate_dest_filename(GLOBAL_LIST_OBJECT[0], GLOBAL_LIST_OBJECT[1])

    #     with TqdmUpTo(unit='B', unit_scale=True, miniters=1, \
    #     desc=url.split('/')[-1]) as t:  # all optional kwargs
    #         local_filename, headers = urllib.request.urlretrieve(url, \
    #         filename=dst, reporthook=t.update_to, data=None)

    #     print("contentlength: ", headers['Content-Length'])
    #     checkfile = open(local_filename)
    #     if checkfile:
    #         tqdm.write(BColors.BOLD + "Download completed!" + BColors.ENDC)
    #     checkfile.close()

    #     if os.path.isfile(local_filename):
    #         return True
    #     else:
    #         return False
    #     return False


    def file_downloader(self, url, destination):
        """Downloads the file at the url passed."""

        print("Destination: ", destination)
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:55.0) \
        Gecko/20100101 Firefox/55.0'}
        request_session = requests.Session()
        request_session.headers.update({'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; \
        rv:55.0) Gecko/20100101 Firefox/55.0'})

        # url="http://httpbin.org/headers" #for testing
        chunk_size = 1024

        req = request_session.get(url, headers=headers, stream=True)
        if req.status_code != 200:
            if TQDM_AVAILABLE:
                tqdm.write(BColors.FAIL + "Error downloading the URL: " + \
                str(req.status_code) + BColors.ENDC)

                GLOBAL_LIST_OBJECT['error'] = str("Error downloading the URL: " + url + \
                " into " + destination + ". Error was:" + str(req.status_code))
                return False
            else:
                print(BColors.FAIL + "Error downloading the URL: " + url + \
                " into " + destination + ". Error was:" + str(req.status_code) + BColors.ENDC)

                GLOBAL_LIST_OBJECT['error'] = str("Error downloading the URL: " + url + \
                " into " + destination + ". Error was:" + str(req.status_code))
                return False

        with open(destination, 'wb') as file_handler:
            if TQDM_AVAILABLE:
                pbar = tqdm(unit="B", total=int(req.headers['Content-Length']))
            for chunk in req.iter_content(chunk_size=chunk_size):
                if chunk: # filter out keep-alive new chunks
                    pbar.update(len(chunk))
                    file_handler.write(chunk)
        if TQDM_AVAILABLE:
            pbar.close()
            tqdm.write(BColors.BOLD + "\nDownload of " + GLOBAL_LIST_OBJECT['parent_dir'] + \
            "/" + GLOBAL_LIST_OBJECT['file_id'] + " completed!" + BColors.ENDC)
        else:
            print(BColors.BOLD + "\nDownload of " + GLOBAL_LIST_OBJECT['parent_dir'] + \
            "/" + GLOBAL_LIST_OBJECT['file_id'] + " completed!" + BColors.ENDC)
        # return destination
        return True


    def generate_dest_filename(self, download_dir, file_id):
        """make final filename for file to be written"""
        try_number = 1
        download_dest = MAIN_OBJ.outputdir + download_dir + os.sep + file_id + ".mp4"

        while os.path.isfile(download_dest):
            download_dest = MAIN_OBJ.outputdir + download_dir + os.sep + \
            file_id + ("_(%s)" %(try_number)) + ".mp4"
            try_number += 1
            if not os.path.isfile(download_dest):
                # We have finally found an unused filename, we keep it
                break
        return download_dest


class GfycatClient(object):
    """credits to https://github.com/ankeshanand/py-gfycat/"""

    def __init__(self):
        pass

    def query_gfy(self, gfyname):
        """Query a gfy name for URLs and more information."""
        request_session = requests.Session()
        request_session.headers.update({'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; \
rv:55.0) Gecko/20100101 Firefox/54.0'})
        req = request_session.get(QUERY_ENDPOINT + gfyname)
        if req.status_code != 200:
            raise GfycatClientError('Unable to query gfycay for the file',
                                    req.status_code)

        return req.json()


class GfycatClientError(Exception):
    """credits to https://github.com/ankeshanand/py-gfycat/"""

    def __init__(self, error_message, status_code=None):
        self.status_code = status_code
        self.error_message = error_message

    def __str__(self):
        if self.status_code:
            return "(%s) %s" % (self.status_code, self.error_message)

        return self.error_message

if __name__ == "__main__":
    MAIN_OBJ = Main()
    MAIN_OBJ.main() # horrible
