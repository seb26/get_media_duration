from __future__ import unicode_literals, print_function
import argparse
import ffmpeg
import sys
from pprint import pprint

path_good_file = "/Users/data/Projects/TESTS/TL short.mov"
path_greyarea_file = "/Users/data/Downloads/test_find_children.cpp.txt"
path_bad_file = "/Users/data/Downloads/ASCFDL_UserGuide_v1.0.pdf"

if __name__ == '__main__':
    try:
        probe = ffmpeg.probe(path_good_file)
    except ffmpeg.Error as e:
        print(e.stderr, file=sys.stderr)
        sys.exit(1)

    print(type(probe))
    pprint(probe)