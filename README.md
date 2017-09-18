Have you downloaded a bunch of webm and gif files from gfycat and 
just realized they store their own mp4 encoded files as well?

This tool scrapes your local directory, makes a list of seemingly gfycraps, 
fetches gfycat servers to see if the file still exist and hasn't been removed,
downloads the correponding mp4 into a directory with the same name as the gfycrap.

To put it simply:
* Lists all potential Gfycat files on local disk
* Fecthes corresponding mp4 file on gfycat servers
* Downloads the file to disk according to the directory layout of local files

Usage:
gfyfetch.py [DIR|TXT]

where DIR is an absolute path to directories holding your gfycraps
or TXT is an absolute path to a text file listing paths to gfycraps 
(the script generates such files to resume operations at a later time if needed)

Only tested on Linux!
