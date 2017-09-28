Have you downloaded a bunch of webm and gif files from gfycat and 
just realized they store their own mp4 encoded files as well?

# Description:
This tool scrapes your local directory, makes a list of seemingly gfycraps, 
fetches gfycat servers to see if the file still exist and hasn't been removed,
downloads the correponding mp4 into a directory with the same name as the gfycrap.

To put it simply:
* Lists all files on local disk that matches gfycat naming scheme via regexp (three words, each with first letter capitalized "AbAbAb.[webm|gif|mp4]")
* Fetches corresponding mp4 file URL on gfycat servers
* Downloads the file to disk according to the directory layout of local files

# Dependencies (optional)
tqdm python lib for progress bar (pip install tqdm)
diffmerge for checking regexp'ed scraped files retained (otherwise will use diff)
vim or any text editor to edit download queue if needed

# Usage:
gfyfetch.py [DIR|TXT]
gfyfetch.py --help

where DIR is an absolute path to directories holding your gfycraps
or TXT is an absolute path to a text file listing paths to gfycraps 
(the script generates such files to resume operations at a later time if needed)

# Disclaimer:
Ugly code in places, sorry I'm still learning.
Only tested on (Arch) Linux, probably works on other OS.
