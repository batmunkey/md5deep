#!/usr/bin/env python

import os
import sys 
import hashlib
import logging
import time

def instantiate_logger():
    global logger
    logger = logging.getLogger("md5deep")
    hdlr = logging.FileHandler("./md5deep.log")
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.INFO)

# Optimized for low-memory systems, read whole file with blocksize=0
def md5sum(filename, blocksize=65536):
    hash = hashlib.md5()
    with open(filename, "rb") as f:
        for block in iter(lambda: f.read(blocksize), ""):
            hash.update(block)
    return hash.hexdigest()

def usage():
    print "Usage: md5deep.py [OPTIONS] [FILES]"
    print "-r        - recursive mode, all subdirectories are traversed."
    print "-X <file> - enables negative matching mode."
    print "-f        - speed up hash calculations, using more memory."
    print "-0        - Uses a NULL character (/0) to terminate each line instead of a newline. Useful for processing filenames with strange characters."
    print "-d        - Destination to check hashes against."

def validate_hashes(hashfile, hashlist):
    # Open file and build a new hashlist
    hashlistrec = []
    with open(hashfile, "r") as f:
        for line in f:
            filehash,filename = line.rstrip().split("  ")
            # Convert to platform covention directory separators
            filename = normfname(filename)
            # Add entry to hashlistrec
            hashlistrec.append((filename, filehash))
        for diff in list(set(hashlistrec) - set(hashlist)):
            # Replicate "-n" md5deep functionality; print only the filename
            # if the file is missing in the filename list; print the hash
            # of the current file if it is different from the negative match
            # file.
            if (not os.path.isfile(diff[0])):
                # File from negative match list is missing, just print filename
                print winfname(diff[0])
            else:
                print diff[0] + "  " + winfname(diff[1])

# Produce a Windows-style filename
def winfname(filename):
    return filename.replace("/","\\")

# Normalize filename based on platform
def normfname(filename):
    if os.name == 'nt': # Windows
        return filename.replace("/", "\\")
    else:
        return filename.replace("\\","/")

def hash_printer(source):
    # Build a list of (hash,filename) for each file, regardless of specified
    # options
    hashlist = []
    # Hash files in the current directory
    for f in source:
        if os.path.isfile(f):
            hashlist.append((f, md5sum(f, md5blocklen)))

    # Walk all subdirectories
    if opt_recursive:
        for start in sys.argv[1:]:
            for (directory, _, files) in os.walk(start):
                for f in files:
                    path = os.path.join(directory, f)
                    hashlist.append((path, md5sum(path, md5blocklen)))

    # With the hashlist built, compare to the negative match list, or print
    # the results.
    if opt_negmatch:
        validate_hashes(opt_negmatch, hashlist)
    else:
        # Just print out the list with Windows-syle filenames
        for hash in hashlist:
           if opt_null:
              print "%s  %s\0"%(hash[1],winfname(hash[0]))
           else:
              print "%s  %s"%(hash[1],winfname(hash[0]))

def compare_hash_arrays(hash_one, hash_two):
    compared_hashes = []
    compared_hashes = [x for x in hash_one if x not in hash_two]
    return compared_hashes

if __name__ == '__main__':
    ip = ""
    uname = ""
    path = ""
    opt_recursive = None
    opt_negmatch = None
    opt_fast = None
    opt_null = None
    opt_dest = None
    opt_files = []
    opt_dest_files = []
    # Default block length to optimize for low-memory systems
    md5blocklen=65536

    if len(sys.argv) == 1:
        usage()
        sys.exit(0)

    args = sys.argv[1:]
    it = iter(args)
    for i in it:
        if i == '-r':
            opt_recursive = True
            opt_files.append(i)
            continue
        elif i == '-0':
            opt_null = True
            continue
        elif i == '-f':
            opt_fast = True
            md5blocklen = 0
        elif i == '-X':
            opt_negmatch = next(it)
            if not os.path.isfile(opt_negmatch):
                sys.stdout.write("Cannot open negative match file %s\n"%opt_negmatch)
                sys.exit(-1)
            continue
        elif i == '-d':
            opt_dest = True
            opt_dest_files.append(i)
            continue    
        else:
            continue

    hash_printer(opt_files)
    hash_printer(opt_dest_files)
    compare_hash_arrays(opt_files, opt_dest_files)
