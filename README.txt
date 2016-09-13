NonRecurrentShuffler v2016.09.13
by Andrew Berge


INFORMATION
    NonRecurrentShuffler (NRS) is for creating music playlists in which no artist plays twice in a row.
    It spreads out each artist's tracks evenly throughout the playlist, so that you hear each artist regularly.
    It can also sort by any other tag you want, such as Genre or Album (documentation assumes Artist, for simplicity).


INSTRUCTIONS
    Create an m3u or m3u8 playlist with other software.
    A simple txt file with a list of files (one per line) will also work.
    Drag the playlist file onto nrs.exe
    
    To sort by a tag other than artist, or change any other options, you'll have to use the command line. See cmdhelp.txt for more details.


NOTES
    The original playlist will be overwritten by default.
    Extended m3u information is not retained.
    The new playlist can be repeated. There will be no recurrences at the beginning or end.
    Having no artist play twice in a row is always possible unless any single artist represents more than 50% of the playlist.
    Files that are missing, unsupported or are missing tags will be treated as "[MISSINGFILE]", "[UNSUPPORTEDFILE]" and "[MISSINGTAG]", respectively. They are retained and spread evenly throughout the playlist.


CREDIT
    This software was written in Python 3.5 (http://www.python.org/).
    It uses the Mutagen module to scan tags (https://bitbucket.org/lazka/mutagen).
    The script was compiled to exe using PyInstaller
    (http://www.pyinstaller.org/)
    Many thanks go to the community at Stack Overflow (http://stackoverflow.com/).


COPYRIGHT

    NonRecurrentShuffler
    MIT License
    http://opensource.org/licenses/MIT

    Python
    Open Source
    http://docs.python.org/2/license.html

    Mutagen
    GNU GPL v2
    http://www.gnu.org/licenses/old-licenses/gpl-2.0.html

    PyInstaller
    GPL license
    https://github.com/pyinstaller/pyinstaller/wiki/License
