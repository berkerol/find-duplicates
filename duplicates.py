#!/usr/bin/python

import os
import re
import hashlib
import argparse
import subprocess
from collections import defaultdict

# Initialize the global variables
# stores all hash to list (files and directories) mappings for checking duplicates
all_hashes = defaultdict(list)
# stores whether file names or directory names will be matched to a pattern
check_pattern = False
current_path = subprocess.check_output("pwd", shell=True).splitlines()[
    0]  # stores the directory where program is running
dirs = []  # list of directories to traverse while searching for duplicates

# Parse the program arguments
parser = argparse.ArgumentParser()
action = parser.add_mutually_exclusive_group()
action.add_argument('-c', action='store', dest='command',
                    help='Apply command to duplicates')
action.add_argument('-p', action='store_true', default=False,
                    dest='print_duplicates', help='Print duplicates')
file_type = parser.add_mutually_exclusive_group()
file_type.add_argument('-f', action='store_true', default=False,
                       dest='check_files', help='Look for duplicate files')
file_type.add_argument('-d', action='store_true', default=False,
                       dest='check_dirs', help='Look for duplicate directories')
parser.add_argument(action='store', nargs='*', dest='dirs',
                    help='Pattern to match and directories to search')

# Check the results of argument parsing and modify the global variables according to the results
results = parser.parse_args()
if not results.command and not results.print_duplicates:
    results.print_duplicates = True  # default option for action
if not results.check_dirs and not results.check_files:
    results.check_files = True  # default option for filtering
if results.dirs:
    for name in results.dirs:
        if "\"" in name:  # find the right element for pattern
            check_pattern = True
            pattern = name[1:-1]  # get rid of the "" or ''
            results.dirs.remove(name)
            break
    for path in results.dirs:
        if current_path in path:
            dirs.append(path)
        else:
            # convert relative paths to absolute paths
            dirs.append(current_path + "/" + path)
if not results.dirs:
    # use current path if there is no directories as arguments
    dirs.append(current_path)

# Recursive method for traversing all contents of the directory.
# param pathname (str) : directory to traverse
# returns (str) : the hash of sorted and concatenated hashes of contents


def dfs(pathname):
    dir_hashes = []
    # print "entered:\t" + pathname
    for filename in os.listdir(pathname):
        newpath = pathname + "/" + filename
        if os.path.isdir(newpath):
            hash = dfs(newpath)
            # print "\tfolder:" + newpath + "\thash:" + hash
        else:
            hash = subprocess.check_output(
                "shasum -a 256 " + "\"" + newpath + "\"", shell=True).split()[0]
            # print "\tfile:" + newpath + "\thash:" + hash
        dir_hashes.append(hash)
        all_hashes[hash].append(newpath)
    # print "exited:\t\t" + pathname
    if not dir_hashes:
        dir_hashes.append("")  # for empty directories
    dir_hashes.sort()
    return hashlib.sha256("".join(map(str, dir_hashes))).hexdigest()


# Traverse all directories
while dirs:
    dfs(dirs.pop())

# Traverse the dictionary for duplicate files and directories and
# process (apply command in program arguments or print) them if they are valid according to the program arguments
for hash, files in all_hashes.iteritems():
    # for not printing empty files or directories
    if len(files) > 1 and hash != hashlib.sha256("").hexdigest():
        duplicates = []
        for file in files:
            if (((results.check_files and os.path.isfile(file)) or (results.check_dirs and os.path.isdir(file)))
                    and ((not check_pattern) or (check_pattern and re.search(pattern, file[file.rfind("/") + 1:])))):
                duplicates.append(file)
        if len(duplicates) > 1:
            duplicates.sort()
            if results.command:
                for duplicate in duplicates:
                    print subprocess.check_output(results.command + " \"" + duplicate + "\"", shell=True)
                print
            if results.print_duplicates:
                for duplicate in duplicates:
                    print duplicate
                print
