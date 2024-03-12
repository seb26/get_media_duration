from os import path
from pathlib import Path
from typing import Generator
import argparse
import json
import logging
import sys

from timecode import Timecode
import ffmpeg

MEDIA_FILE_EXTENSIONS = [ '264', '265', '266', '3g2', '3gp', 'amv', 'asf', 'avi', 'f4a', 'f4b', 'f4p', 'f4v', 'flv', 'flv', 'gifv', 'm4p', 'm4v', 'm4v', 'mkv', 'mng', 'mod', 'mov', 'mp2', 'mp4', 'mpe', 'mpeg', 'mpg', 'mpv', 'mxf', 'nsv', 'ogg', 'ogv', 'qt', 'rm', 'roq', 'rrc', 'svi', 'vob', 'webm', 'wmv', 'yuv' ]

class MediaFile(object):
    def __init__(self, filepath: str, probe: dict):
        self._probe = probe
        self.duration_sec = None
        self.duration_timecode = None
        self.file_duration_sec = None
        self.filepath = filepath
        self.fps = None
        self.frame_count = None
        self.valid = False
        try:
            self.file_duration_sec = float(self._probe['format']['duration'])
            video_stream = next((stream for stream in self._probe['streams'] if stream['codec_type'] == 'video'), None)
            if video_stream is None:
                logger.error(f"{filepath}\n    Skipped. No video stream for this file.")
            # Frame count
            self.frame_count = int(video_stream['nb_frames'])
            # FPS
            num, denom = video_stream['r_frame_rate'].split('/')
            self.fps = int( float(num) * float(denom) )
            # TODO check that video frame count and file duration correspond
            # Duration
            self.duration_sec = float(video_stream['duration'])
            # Adjust for timecode library being weird
            adjustment = 1
            self.duration_timecode = Timecode(self.fps, frames=self.frame_count + adjustment)
        except Exception as e:
            logger.error(f"{filepath}\n    Skipped. Exception while getting metadata about this file - {e}")
            logger.debug(e, exc_info=1)
        if self.frame_count and self.fps and self.duration_timecode:
            self.valid = True
        else:
            self.valid = False

    def get(filepath: str):
        try:
            probe = ffmpeg.probe(filepath)
            if probe:
                return MediaFile(filepath, probe)
        except Exception as e:
            logger.error(f"{filepath}\n    Skipped. Exception - {e}")
            logger.debug(e, exc_info=1)
        return False
        
def display_frames_to_tc(fps, frames: int) -> str:
    """Use to display an amount of frames in HH:MM:SS:FF - use only for display!!!!!
    - Due to the usual functionality in Timecode library producing values that are 1 frame short!
    atm idk why"""
    return Timecode(fps, frames=frames + 1)
    
def has_media_file_extension(filepath: str) -> bool:
    """If the extension is in list of extensions associated with ffmpeg support"""
    ext = filepath.suffix
    return ( ext.lower()[1:] in MEDIA_FILE_EXTENSIONS )

def get_media_filepaths(input):
    if isinstance(input, str):
        if path.isfile(input):
            filepath = Path(input)
            if has_media_file_extension(filepath):
                yield filepath
        elif path.isdir(input):
            dirpath = Path(input)
            for item in dirpath.iterdir():
                filepath = Path.joinpath(dirpath, item)
                if has_media_file_extension(filepath):
                    yield filepath
    elif isinstance(input, Generator):
        for filepath in input:
            if has_media_file_extension(filepath):
                yield filepath

def analyse(input_items) -> dict:
    media_filepaths = get_media_filepaths(input_items)
    result = {
        'count_files_skipped': 0,
        'count_files': 0,
        'count_framerates': {},
        'files': [],
        'count_frames': 0,
        'count_frames_by_framerate': {},
    }
    for filepath in media_filepaths:
        mf = MediaFile.get(filepath)
        if isinstance(mf, MediaFile):
            if mf.valid is True:
                filename = filepath.name
                # Per this file
                result['files'].append({
                    'filepath': filepath,
                    'fps': mf.fps,
                    'frame_count': mf.frame_count,
                    'duration_timecode': display_frames_to_tc(mf.fps, mf.frame_count),
                })
                logger.info(f"{filepath}\n    FPS: {mf.fps} | Frames: {mf.frame_count:,} | Duration: {mf.duration_timecode}")
                # Summaries
                result['count_files'] += 1
                result['count_frames'] += mf.frame_count
                if mf.fps not in result['count_framerates']:
                    result['count_framerates'][mf.fps] = 1
                else:
                    result['count_framerates'][mf.fps] += 1
                if mf.fps not in result['count_frames_by_framerate']:
                    result['count_frames_by_framerate'][mf.fps] = mf.frame_count
                else:
                    result['count_frames_by_framerate'][mf.fps] += mf.frame_count
                continue
        result['count_files_skipped'] += 1
    return result

def summary_output(
        count_files_skipped: int,
        count_files: int,
        count_framerates: dict,
        count_frames_by_framerate: dict,
        count_frames: int,
        **kwargs,
    ):
    total_duration_timecode = None
    total_duration_timecode_fps = None
    if len(count_framerates) > 0:
        framerates_found_output = ', '.join( str(i) for i in sorted( count_framerates.keys() ) )
        sum_durations_lines = []
        for fps, count_frames in count_frames_by_framerate.items():
            line = f"{display_frames_to_tc(fps, count_frames)} @ {fps} FPS"
            sum_durations_lines.append(line)
        sum_durations = '\n                      '.join(sum_durations_lines)
    tally_output = f"""
    Files counted:    {count_files}
    Files skipped:    {count_files_skipped}
    Framerates found: {len(count_framerates)} ({framerates_found_output})

    Total framecount: {count_frames:,}
    Total duration:   {sum_durations}
    """
    return tally_output

if __name__ == '__main__':
    logger = logging.getLogger('framecount')
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    handler_stdout = logging.StreamHandler(stream=sys.stdout)
    handler_stdout.setLevel(logging.INFO)
    handler_stderr = logging.StreamHandler(stream=sys.stderr)
    handler_stderr.setLevel(logging.DEBUG)
    handler_stderr.addFilter(lambda record: record.levelno >= logging.INFO)

    parser = argparse.ArgumentParser(description='Outputs the frame count, FPS and duration of a given media file or folder or files, and a summary of their total duration')
    parser.add_argument('input_items', help='File or folder path(s) pointing to media files')
    parser.add_argument('--quiet', help='Output only the summary', action='store_true')
    parser.add_argument('--count', help='Output only the frame count', action='store_true')
    parser.add_argument('--json', help='Output JSON result', action='store_true')
    args = parser.parse_args()

    if args.quiet or args.json or args.count:
        logger.setLevel(logging.ERROR)
    else:
        logger.setLevel(logging.INFO)

    media_filepaths = get_media_filepaths(args.input_items)
    result = analyse(media_filepaths)
    
    if args.json:
        if args.count:
            output = json.dumps( {
                'count_frames': result['count_frames'],
                'count_frames_by_framerate': result['count_frames_by_framerate']
            } )
            print(output)
        else:
            output = json.dumps(
                result,
                sort_keys = True,
                default = str,
            )
            print(output)
    else:
        if args.count:
            print(result['count_frames'])
            raise SystemExit
        else:
            output = summary_output(**result)
            print(output)
    
    

    

        

