import argparse
import ffmpeg
from pathlib import Path
from pprint import pprint
from os import path
from typing import Union
import logging

from timecode import Timecode

logger = logging.getLogger('framecount')
logging.basicConfig(level=logging.INFO, format='%(message)s')

MEDIA_FILE_EXTENSIONS = [ 'mp4', 'mov' ]

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
        
def has_media_file_extension(filepath: str):
    """If the extension is in list of extensions associated with ffmpeg support"""
    ext = filepath.suffix
    return ( ext.lower()[1:] in MEDIA_FILE_EXTENSIONS )

def get_media_filepaths(input: Union[str, list]):
    if isinstance(input, str):
        if path.isfile(input):
            filepath = Path(input)
            if has_media_file_extension(filepath):
                yield filepath
            else:
                return
        elif path.isdir(input):
            dirpath = Path(input)
            for item in dirpath.iterdir():
                filepath = Path.joinpath(dirpath, item)
                if has_media_file_extension(filepath):
                    yield filepath
                else:
                    return
        return

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Gets frame count, FPS and duration of a given media file or folder or files')
    parser.add_argument('input_items', help='File or folder path(s) pointing to media files')
    args = parser.parse_args()
    if args.input_items:
        media_filepaths = get_media_filepaths(args.input_items)
        count_files = 0
        count_files_skipped = 0
        fps_found = {}
        sum_frames = 0
        for filepath in media_filepaths:
            mf = MediaFile.get(filepath)
            if isinstance(mf, MediaFile):
                if mf.valid is True:
                    filename = filepath.name
                    # Per this file
                    logger.info(f"{filepath}\n    FPS: {mf.fps} | Frames: {mf.frame_count:,} | Duration: {mf.duration_timecode}")
                    # Tallies
                    count_files += 1
                    sum_frames += mf.frame_count
                    if mf.fps not in fps_found:
                        fps_found[mf.fps] = 1
                    else:
                        fps_found[mf.fps] += 1
                    continue
            count_files_skipped += 1
        # Print tallies
        fps_found_output = ', '.join( str(i) for i in sorted( fps_found.keys() ) )
        total_duration_timecode = None
        total_duration_timecode_fps = None
        if len(fps_found.keys()) > 0:
            total_duration_timecode_fps = max(fps_found, key=fps_found.get)
            # adjustment for timecode library weirdness
            adjustment = 1
            total_duration_timecode = Timecode(total_duration_timecode_fps, frames=sum_frames + adjustment)
        tally_output = f"""
        Files counted:    {count_files}
        Files skipped:    {count_files_skipped}
        Framerates found: {fps_found_output}

        Total framecount: {sum_frames:,}
        Total duration:   {total_duration_timecode} @ {total_duration_timecode_fps} FPS
        """
        print(tally_output)

        

        

