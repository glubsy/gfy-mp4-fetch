#!/usr/bin/python3
""" download from file list
usage: script [input_file]
"""
import os
import subprocess
import shutil
import sys
import signal
import time
import requests
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
# DEBUG
# shutil.copy("/data1TB/CGI_fix/gfy_test.txt", "/tmp/gfy_test.txt")
# INPUTLIST = "/tmp/gfy_test.txt"
# OUTPUTLIST = "/tmp/gfyfetch_downloads_sucess.txt"

ARGV1_PATH =  os.path.abspath(os.path.join(os.path.abspath(sys.argv[1]), os.pardir))
INPUTLIST = os.path.abspath(sys.argv[1])
SED_FOUND = True if os.path.exists(str(shutil.which("sed"))) else False
CURRENT_TUPLE = {"parent_dir": "", "file_id": "", "url": ""}
OUTPUTLIST = ARGV1_PATH + "/gfyfetch_downloads_success.txt"
CURL_LOGFILEPATH = "/tmp/gfyfetch_download_error_log.txt"

# if os.path.exists(str(INPUTLIST + ".BAK")):
#     shutil.copy(str(INPUTLIST + ".BAK") , INPUTLIST)
shutil.copy(INPUTLIST, str(INPUTLIST + ".BAK"))

if os.path.exists(CURL_LOGFILEPATH):
    os.remove(CURL_LOGFILEPATH)

def main():
    """Main loop"""
    PREVIOUS_TARGETDIR = ""
    TARGETDIR = ""
    BASEOUTPUTDIRPATH = ARGV1_PATH
    os.chdir(BASEOUTPUTDIRPATH)
    CWD = os.getcwd()

    while True:

        read_line(INPUTLIST)

        firstmesg = "File " + CURRENT_TUPLE['parent_dir'] + "/" + CURRENT_TUPLE['file_id']
        write_string_to_file(firstmesg, OUTPUTLIST)

        TARGETDIR = BASEOUTPUTDIRPATH + os.sep + CURRENT_TUPLE['parent_dir']

        if os.path.normpath(TARGETDIR) not in os.path.normpath(PREVIOUS_TARGETDIR): #don't move
            while os.path.normpath(CWD) != os.path.normpath(TARGETDIR):
                if os.path.normpath(CWD) == os.path.normpath(BASEOUTPUTDIRPATH): # at base
                    #go down
                    CWD = change_dir(CWD + os.sep + CURRENT_TUPLE['parent_dir'])
                elif os.path.normpath(CWD) == os.path.normpath(TARGETDIR):
                    break
                else:
                    #go up
                    CWD = change_dir(os.path.abspath(os.path.join(CWD, os.pardir))) #parent dir
        else: # we stay, same dir
            pass

        read_line(INPUTLIST, 1) #read second line
        # curlret = call_curl_failed(CURRENT_TUPLE['url'], CURL_LOGFILEPATH)
        # if curlret == 0:
        #     write_success_to_log(OUTPUTLIST)
        # elif curlret == 22: #404
        #     write_failure_to_log(OUTPUTLIST, notfound=True)
        # else:
        #     write_failure_to_log(OUTPUTLIST)
        reqret = file_downloader(CURRENT_TUPLE['url'], str(os.path.abspath(CWD) \
        + os.sep + CURRENT_TUPLE['url'].split("/")[-1]))
        # + os.sep + CURRENT_TUPLE['url'].split("/")[-1]))
        if reqret == 0:
            write_success_to_log(OUTPUTLIST)
        else: #404 or something
            write_failure_to_log(OUTPUTLIST, reqret)
        remove_first_two_lines(INPUTLIST)
        PREVIOUS_TARGETDIR = TARGETDIR
        CURRENT_TUPLE['parent_dir'] = ""
        CURRENT_TUPLE['file_id'] = ""
        CURRENT_TUPLE['url'] = ""

        time.sleep(2)

    print("Exiting main() loop.")
    sys.exit(0)


def exit_gracefully(signum, frame):
    # restore the original signal handler as otherwise evil things will happen
    # in raw_input when CTRL+C is pressed, and our signal handler is not re-entrant
    signal.signal(signal.SIGINT, original_sigint)
    
    try:
        if input("\nReally quit? (y/n)> ").lower().startswith('y'):
            sys.exit(1)

    except KeyboardInterrupt:
        print("Ok ok, quitting")
        sys.exit(1)

    # restore the exit gracefully handler here    
    signal.signal(signal.SIGINT, exit_gracefully)


def change_dir(path):
    """change working dir,
    push previous dir to stack"""
    # PREVIOUS_WD = os.getcwd()
    # DIR_STACK.append(PREVIOUS_WD)
    if not os.path.isdir(path):
        os.makedirs(path)
    os.chdir(path)
    # print("changed dir to: " + path)
    return os.getcwd()


def read_line(file, linenum=0):
    """If line starts with File, returns tuple CURRENT_TUPLE['parent_dir', 'file_id']
    if line starts with http, returns CURRENT_TUPLE['url']"""
    try_open_remove(file)

    with open(file, 'r') as file_handler:
        if not linenum: #read first line
            return parse_current_line(file_handler.readline())#[1:]
        else: #read second line
            file_handler.readline() #jump over first line
            return parse_current_line(file_handler.readline())


def try_open_remove(file):
    try:
        if os.stat(file).st_size == 0:
            os.remove(file)
            print("End of file listing. Exiting.")
            exit(0)
    except OSError as err:
        print("Read first line error:", err)
        exit(1)


def parse_current_line(theline):

    if theline[0] == "F": #starts with File
        strtosplit = theline.split(" ")[1]
        splits = strtosplit.split("/")
        CURRENT_TUPLE['parent_dir'] = splits[0]
        CURRENT_TUPLE['file_id'] = splits[1]
    elif theline[0] == "h": #start with http
        theline = theline.rstrip()
        CURRENT_TUPLE['url'] = str(theline)
    else:
        print("ERROR parsing:", theline)
        sys.exit(1)


def remove_first_two_lines(file):
    """Remove the first line from file.
    First, check if sed exists on the PATH
    or remove first line ourselves manually"""

    if not SED_FOUND:
        with open(file, 'r') as file_handler_in:
            data = file_handler_in.read().splitlines(True)
        with open(file, 'w') as file_handler_out:
            file_handler_out.writelines(data[1:])
    else:
        cmd = ['sed', '-i', '-e', '1,2d', file]
        subprocess_call = subprocess.Popen(cmd, shell=False, \
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = subprocess_call.communicate()
        if err:
            raise NameError(
                '\n============= WARNING/ERROR ===============\n{}\n\
===========================================\n'.format(err.rstrip()))
        #return out


def write_success_to_log(file):
    message = "has a new source:\n" + CURRENT_TUPLE['url'] + \
    "\nDownload OK\nSuggesting removal of:\n"\
    + CURRENT_TUPLE['file_id'] + \
    "\n=========================================================================="
    write_string_to_file(message, file)
    print(BColors.OKGREEN + "Download OK for:\n" + CURRENT_TUPLE['url'] + \
    "\n==========================================================================" + BColors.ENDC)


def write_failure_to_log(file, reqcode):
    message = "has a new source:\n" + CURRENT_TUPLE['url'] + "\nDownload FAILED\n" \
    + "Status code: " + str(reqcode) + "\nFor "\
    + CURRENT_TUPLE['file_id'] + \
    "\n=========================================================================="
    write_string_to_file(message, file)
    print(BColors.FAIL + BColors.BOLD + "Download FAILED for:\n" + CURRENT_TUPLE['url'] + \
    "\n==========================================================================" + BColors.ENDC)


def write_string_to_file(string, file, newline=True):
    """Write string to file, appends newline"""

    with open(file, 'a') as file_handler:
        if newline:
            file_handler.write("%s\n" % string)
            #file_handler.write("{}\n".format(item))
        else:
            file_handler.write(string)


def call_curl_failed(url, logfilepath): #not used
    """use curl to download and log everything into logfilepath"""
    print(BColors.BOLD + "CURL DOWNLOADING: " + str(url) + BColors.ENDC)
    with open(logfilepath, 'a') as logfile:
        try:
            cmd = ['curl', '-v', '-O', '-L', '-f', '-C', '-', url]
            # cmd = ['wget', url]
            # subprocess_call = subprocess.Popen(cmd, shell=,False, stdout=logfile, stderr=logfile)
            subprocess_call = subprocess.Popen(cmd, bufsize=1, shell=False, \
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)

            for line in subprocess_call.stdout:
                # sys.stdout.write(line) #comment out if stdout is too clogged
                logfile.write(line)
            out, err = subprocess_call.communicate()
            # ret_code = subprocess_call.wait()
            ret_code = subprocess_call.wait()
            print(BColors.BOLD + "Curl return code: " + str(ret_code) + BColors.ENDC)
            return ret_code
        except Exception as e:
            print(BColors.FAIL + "Exception with curl: " + str(e) + BColors.ENDC)
            return 1
        return 1
    return 1

def file_downloader(url, destination):
    """Downloads the file at the url passed."""

    print("Destination: ", destination)
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:55.0) \
    Gecko/20100101 Firefox/55.0'}
    request_session = requests.Session()
    request_session.headers.update({'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; \
    rv:55.0) Gecko/20100101 Firefox/55.0'})

    # url="http://httpbin.org/headers" #for testing
    chunk_size = 1024

    req = request_session.get(url, headers=headers, stream=True, allow_redirects=True)
    if req.status_code != 200:
        if TQDM_AVAILABLE:
            tqdm.write(BColors.FAIL + "Error downloading the URL: " + \
            str(req.status_code) + BColors.ENDC)
        else:
            print(BColors.FAIL + "Error downloading the URL: " + url + \
            str(req.status_code) + BColors.ENDC)
        return req.status_code

    myCLheader = 0
    for key, value in req.headers.items():
        if "content-length" in key:
            mysize = (int(value)/1000000)
            print("File size: " + str(mysize) + "MB")
            myCLheader = int(value)

    with open(destination, 'wb') as file_handler:
        if TQDM_AVAILABLE:
            # WARNING: if gfycat decides one day to stop giving content-length in headers... ouch
            pbar = tqdm(unit="KB", total=myCLheader)
        for chunk in req.iter_content(chunk_size=chunk_size):
            if chunk: # filter out keep-alive new chunks
                pbar.update(len(chunk))
                file_handler.write(chunk)
    if TQDM_AVAILABLE:
        pbar.close()
        tqdm.write(BColors.BOLD + "\nDownload of " + CURRENT_TUPLE['parent_dir'] + \
        "/" + CURRENT_TUPLE['file_id'] + " completed!" + BColors.ENDC)
    else:
        print(BColors.BOLD + "\nDownload of " + CURRENT_TUPLE['parent_dir'] + \
        "/" + CURRENT_TUPLE['file_id'] + " completed!" + BColors.ENDC)
    # return destination
    return 0


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


if __name__ == "__main__":
    original_sigint = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, exit_gracefully)
    main()
