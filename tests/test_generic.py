from get_media_duration import *

from pathlib import PosixPath
from pprint import pprint

import json

user_input = 'tests/sample_files'

a = get_media_filepaths(user_input)

b = {
                    'count_files_skipped': 0,
                    'count_files': 1,
                    'count_framerates': { 25: 1 },
                    'count_frames': 750,
                    'count_frames_by_framerate': {25: 750},
                    'files': [{
                        'filepath': PosixPath('tests/sample_files/file_25p_30sec.mov'),
                        'fps': 25,
                        'frame_count': 750,
                        'duration_timecode': '00:00:30:00',
                    }],
                }

x = probe_filepaths(a)

pprint(a)
pprint(x)
pprint(b)

print( 'x hash', hash( json.dumps(x, sort_keys=True, default=str) ) )
print( 'b hash', hash( json.dumps(b, sort_keys=True, default=str) ) )

# assert x == b

print('11')