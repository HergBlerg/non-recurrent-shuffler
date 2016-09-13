# -*- coding: utf-8 -*-
"""
    Name: NonRecurrentShuffler
    Version: 2016.09.13
    Author: Andrew Berge
    Description: Shuffles playlists so that the same artist doesn't play twice in a row. Also supports other tags, such as genre.
    
    Python v3.5.2

    Known bugs:
        None for now.
"""

# Comments assume we're sorting the %artist% tag for simplicity's sake.

# DEFINE FUNCTIONS
def getFileTag(file, tag):
    # Returns the value of a given tag in a given file.
    # Input: file (including path and extension), desired tag.
    try:
        f = mutagen.File(file, easy=True)
        try: tag = f[tag]
        except KeyError:
            tag = ["[MISSINGTAG]"]
        except TypeError:
            tag = ["[UNSUPPORTEDFILE]"]
    except FileNotFoundError:
        tag = ["[MISSINGFILE]"]
        DeadLinks.append(file)
    except OSError:
        tag = ["[MISSINGFILE]"]
        DeadLinks.append(file)
    return tag

def getDictMax(dict):
    # Returns the key with the highest value in a dictionary.
    # Value must at least 0

    MaxValue = 0
    for Key in dict:
        if dict[Key] >= MaxValue:
            MaxValue = dict[Key]
            MaxKey = Key
    return MaxKey

def uniASCII(string):
    # Encoding is a nightmare.
    # This encodes a string to ASCII, and removes the b' ' to keep things legible.
    return str(string.encode('ascii', 'replace'))[2:-1]

# DEFINE CLASSES
class File:
    def __init__(self,path,tag):
        self.path = path
        self.tag = tag


"""
GET THIS PARTY STARTED
"""
# import modules
# argparse for parsing options from the command line
# mutagen for scanning tags
# random for shuffling the playlist
import argparse, mutagen, random
# error is set to 1 if there are too many of any single tag (>50% of playlist)
error = 0
# debug prints extra stuff if true
debug = 0
# DeadLinks is a list of files that can't be accessed. It will hopefully stay empty.
DeadLinks = []

# Set parameters. Parse command line arguments.
parser = argparse.ArgumentParser()
parser.add_argument('InputFile', help='input playlist file')
parser.add_argument('-b', action='store_false', help='disable BOM')
parser.add_argument('-o', default=0, help='output playlist file')
parser.add_argument('-s', action='store_false', help='disable shuffle')
parser.add_argument('-t', default='artist', help='tag to sort by')
parser.add_argument('-v', action='store_true', help='enable verbose ouput')
cmdline = parser.parse_args()
"""
SO. Now we have our user's variables:
cmdline.InputFile -> our input playlist
cmdline.b -> whether to add a BOM to the output file (1) or not (0)
cmdline.o -> our output playlist (or 0, in which case we overwrite the input)
cmdline.s -> whether we should shuffle the playlist (1) or only sort it (0)
cmdline.t -> the tag to sort by
cmdline.v -> whether to be verbose (1) or not (0)
"""

# print job details if verbose is true
print('NRS v2016.09.13')
if cmdline.v == 1:
    print('Input: ' + str(cmdline.InputFile))
    if cmdline.o == 0:
        print('Output: overwrite original')
    else:
        print('Output: ' + str(cmdline.o))
    print('Sort by: ' + str(cmdline.t))
    if cmdline.b == 0:
        print('Disable BOM')
    if cmdline.s == 0:
        print('Disable shuffle')
    print('')

# open InputFile. Add each line to a list. Close InputFile.
if cmdline.v == 1: print('Reading input file.')
try:
    InputFile = open(cmdline.InputFile,mode='r', encoding='utf-8-sig')
    InputPlaylist = InputFile.read()
except UnicodeDecodeError:
    InputFile = open(cmdline.InputFile,mode='r')
    InputPlaylist = InputFile.read()
InputPlaylist = InputPlaylist.splitlines()
InputFile.close()
# remove linebreaks and any whitespace there may be in each line.
for line in range(len(InputPlaylist)):
    InputPlaylist[line] = InputPlaylist[line].rstrip()
    
# InputPlaylist should now be a list of filenames. All accessible, all in the original order. Shuffle it if necessary.
if cmdline.s == 1: random.shuffle(InputPlaylist)

# Let's convert this list of filenames into a list of File objects, with path AND tag info. At the same time we'll make a dictionary containing all our artists and the number of each.
TagCount = {}
for f in range(len(InputPlaylist)):
    t = getFileTag(InputPlaylist[f],cmdline.t)[0]
    InputPlaylist[f] = File(InputPlaylist[f],t)
    if t in TagCount:
        TagCount[t] += 1
    else:
        TagCount[t] = 1

"""
OKAY.
Now we have the list InputPlaylist, whch is the original playlist, in the original order, minus dead links.
Each item in the list is an object with path and tag values.
We also have a dictionary TagCount, which tells us how many of each tag there are.
"""

# check if it's possible to make the playlist non-recurrent. Warn if not. Set a flag for use later.
t = getDictMax(TagCount)
if TagCount[t] > len(InputPlaylist)/2:
    error = 1
    print("Warning: More than half the tracks have the tag: " + uniASCII(t))

# if verbose is true, break down how many of each tag there is.
if cmdline.v == 1:
    print("\nThere are " + str(len(InputPlaylist)) + " entries with " + str(len(TagCount)) + " different tags:")
    # make a copy of the tagcount dict. we're going to sort, print and destroy it.
    # d is for dictionary. t is for tag.
    d = TagCount.copy()
    while len(d) > 0:
        t = getDictMax(d)
        print (uniASCII(t) + ": " + str(d[t]))
        del d[t]
    print("Sorting.\n")

"""
OKAY! Time to start sorting.

Here's how it's done:
We take each artist, one at a time, ordered from most entries to least.
You put the big rocks in first to make sure there's room for everything, you know?

So we take the total number of spaces in the playlist, divide by the artist's number of entries, and place the artist in the playlist at the resulting interval. All spread out nice and evenly.

Now things get a bit more complicated.
Next artist, we take only the REMAINING total spaces left, and divide.
We place the artist at regular intervals in the remaing spaces. Only counting the *empty* spaces between each. As if the first artist and it's spaces didn't exist.
Keep doing this with each artist until the playlist is full.

This system works very well 95% of the time, but there are exceptions that will mess it up (tag number combinations like 9, 9, 1). So, as we place our artists, we'll also check the spaces before and after to make sure there's no recurrence. If there is, just move on to the next empty space.

More notes:
We'll randomise the starting point of each artist, so the the most popular doesn't always play first.
Also, we'll only put the artist name in the playlist at first. Only once it's finished will we switch them for filenames. This is in case the shuffle option is disabled and the files have to stay in order.

Got all that?
"""

# make a variable that keeps track of how many spaces are left in the playlist
SpacesRemaining = len(InputPlaylist)
# Let's make our output playlist, full of blank spaces.
OutputPlaylist = ["[BLANKSPACE]"] * SpacesRemaining
lenOutputPlaylist = len(OutputPlaylist)
# Let's make a disposable dictionary again so we can sort/destroy it
d = TagCount.copy()

# while the playlist still has empty spaces
while SpacesRemaining > 0:
    # find the most popular Tag
    t = getDictMax(d)
    # find it's frequency
    f = SpacesRemaining/d[t]
    # choose a random starting point
    randstart = int(round(random.random() * lenOutputPlaylist-1))
    # we're gonna have to iterate through the playlist a lot. make variables to track our position in the playlist, and our position in our imaginary blank-spaces-only playlist (IBSO from this point on)
    plstpos = randstart
    blnkpos = 0
    # for every entry by this artist
    for x in range(0, d[t]):
        # find it's position
        p = round(x * f) % lenOutputPlaylist
        if p < blnkpos:
            blnkpos = 0
            plstpos = randstart
        while True:
            # iterate through the playlist, if a space is blank, we can potentially put our tag there, it's also part of our IBSO playlist.
            if OutputPlaylist[plstpos] == "[BLANKSPACE]":
                # check if we're at the right position in IBSO
                if blnkpos >= p:
                    # if it's not possible to avoid recurrences, don't bother checking surroundings, just put the tag there. Otherwise check surroundings.
                    if error == 1:
                        OutputPlaylist[plstpos] = t
                        SpacesRemaining -= 1
                        # move one step forward in both playlists, break and move on to the next entry for this artist.
                        blnkpos = (blnkpos + 1) % lenOutputPlaylist
                        plstpos = (plstpos + 1) % lenOutputPlaylist
                        break
                    elif (OutputPlaylist[(plstpos-1) % lenOutputPlaylist]) != t and (OutputPlaylist[(plstpos+1) % lenOutputPlaylist]) != t:
                        OutputPlaylist[plstpos] = t
                        SpacesRemaining -= 1
                        # move one step forward in both playlists, break and move on to the next entry for this artist.
                        blnkpos = (blnkpos + 1) % lenOutputPlaylist
                        plstpos = (plstpos + 1) % lenOutputPlaylist
                        break
                # we found a blank spot but it's not our entry's position. Move on.
                blnkpos = (blnkpos + 1) % lenOutputPlaylist
            # this spot is already filled. Move on.
            plstpos = (plstpos + 1) % lenOutputPlaylist
    # all entries for this artist have been placed. Delete the artist from the dict and move on to the next.
    del d[t]
# all artists and their entries have been placed.

# If DeadLinks contains any files, warn the user.
if len(DeadLinks) > 0:
    if cmdline.v == 1:
        print(str(len(DeadLinks)) + " of " + str(len(InputPlaylist)+len(DeadLinks)) + " tracks could not be accessed:")
        for line in DeadLinks:
            print(uniASCII(str(line)))
        print ("")
    else:
        print(str(len(DeadLinks)) + " of " + str(len(InputPlaylist)+len(DeadLinks)) + " tracks could not be accessed.")

# check for recurrences.
r = 0
for x in range(lenOutputPlaylist):
    if debug == 1: print(uniASCII(str(OutputPlaylist[x])))
    if OutputPlaylist[x] == OutputPlaylist[x-1]:
        r += 1
print(str(r) + " recurrences detected.")

# now just replace each artist with a filename.
# for each entry in the output playlist
for x in range(lenOutputPlaylist):
    # get the tag
    t = OutputPlaylist[x]
    # iterate through the input playlist, find the first file with that tag
    for y in range(lenOutputPlaylist):
        if InputPlaylist[y].tag == t:
            # replace the tag in the output playlist with the filename
            OutputPlaylist[x] = InputPlaylist[y].path
            # delete the entry from the input playlist so it doesn't get entered again, we don't need that list any more after this.
            del InputPlaylist[y]
            break

# all that's left is to write our filenames to a file
# create and open a new file for writing in.
# check if we want a BOM or not
if cmdline.b == 0:
    e = "utf-8"
else:
    e = "utf-8-sig"
# check if we overwrite the old file or create a new one
if cmdline.o == 0:
    f = open(cmdline.InputFile, mode='w', encoding=e)
else:
    f = open(cmdline.o, mode='w', encoding=e)
# write the file
for i in OutputPlaylist:
    f.seek(0,2)
    f.write(i + "\n")
# close the file.
f.close()



# we're done here
print(str(lenOutputPlaylist) + " files processed.")
if r > 0 or len(DeadLinks) > 0:
    print("Finished with errors.")
else:
    print("Finished.")


















