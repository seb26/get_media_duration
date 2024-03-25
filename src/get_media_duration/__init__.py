from os import path
from pathlib import Path
from typing import Generator, Union, Iterable
import argparse
import importlib_metadata
import json
import logging
import sys

from timecode import Timecode
import ffmpeg

logger = logging.getLogger(__name__)

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
            probe = ffmpeg.probe(
                filepath,
                hide_banner = None,
            )
            if probe:
                return MediaFile(filepath, probe)
        except Exception as e:
            logger.error(f"{filepath}\n    Skipped. Exception - {e} - {e.stderr}")
            logger.debug(e.stderr, exc_info=1)
        return False

def display_frames_to_tc(fps, frames: int, **kwargs) -> str:
    """Use to display an amount of frames in HH:MM:SS:FF - use only for display!!!!!
    - Due to the usual functionality in Timecode library producing values that are 1 frame short!
    atm idk why"""
    return str(Timecode(fps, frames=frames + 1, **kwargs))
    
def has_media_file_extension(filepath: Path) -> bool:
    """If the extension is in list of extensions associated with ffmpeg support"""
    ext = filepath.suffix
    return ( ext.lower()[1:] in MEDIA_FILE_EXTENSIONS )

def get_media_filepaths(
    input: Union[str, Iterable],
    allow_all: bool = False,
    recurse: bool = False,
) -> Generator:
    """
    Return Path()s of files and folders that are recognised media files, determined by file extension

    :param input: Path()s in a string or Iterable
    :param allow_all: Skip file extension check and pass all items. Default is False
    :param recurse: deeply recurse all folders found and return all items beneath this path in the filesystem.
                    Default is False and will just return files that are immediate children
    """
    def _iterate(filepath: Path):
        if filepath.is_file():
            if has_media_file_extension(filepath) or allow_all:
                yield filepath
        elif filepath.is_dir():
            for child in filepath.iterdir():
                childpath = Path(child)
                if has_media_file_extension(childpath) or allow_all:
                    yield childpath
                if recurse is True:
                    if childpath.is_dir():
                        yield from _iterate(childpath)
    if isinstance(input, str):
        filepath = Path(input)
        yield from _iterate(filepath)
    elif isinstance(input, Iterable):
        for input_item in input:
            filepath = Path(input_item)
            yield from _iterate(filepath)

def probe_filepaths(
    media_filepaths: Generator,
    include_probe: bool = False,
) -> dict:
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
                data = {
                    'filepath': filepath,
                    'fps': mf.fps,
                    'frame_count': mf.frame_count,
                    'duration_timecode': display_frames_to_tc(mf.fps, mf.frame_count),
                }
                if include_probe:
                    data['probe'] = mf._probe
                result['files'].append(data)
                logger.info(f"{filepath}\n    Frames: {mf.frame_count:,} | Duration: {mf.duration_timecode} | FPS: {mf.fps} ")
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
    framerates_found_output = None
    if len(count_framerates) > 0:
        framerates_found_output = "(" + ', '.join( str(i) for i in sorted( count_framerates.keys() ) ) + ")"
        lines_durations_by_fr = []
        for fps, count_frames in count_frames_by_framerate.items():
            line = f"{display_frames_to_tc(fps, count_frames)} @ {fps} FPS"
            lines_durations_by_fr.append(line)
        durations_by_fr = '\n                         '.join(lines_durations_by_fr)
    summary = "\n"
    summary +=       f"    Files counted:       {count_files}"
    if count_files_skipped > 0:
        summary += f"\n    Files skipped:       {count_files_skipped}"
    if len(count_framerates) > 0:
        summary += f"\n    Framerates found:    {len(count_framerates)} {framerates_found_output}"
    if count_frames > 0:
        summary += f"\n    Total framecount:    {count_frames:,}"
    if len(count_frames_by_framerate) > 0:
        summary += f"\n    Total duration:      {durations_by_fr}"
    return summary

def main():
    version = importlib_metadata.version('get_media_duration')
    parser = argparse.ArgumentParser(
        prog = f'get_media_duration (v{version})',
        description=f"Outputs the frame count, framerate (FPS) and time duration of a given media file or folder or files, and a summary of totals.",
    )
    parser.add_argument('--version', help='show version', action='version', version=version)
    parser.add_argument('items', help='file or folder path(s) pointing to media files. For folders, will only traverse only 1 level', nargs='*')
    parser.add_argument('--allow-all', help='assess files of all extensions', action='store_true')
    parser.add_argument('--count', help='output only the frame count', action='store_true')
    parser.add_argument('--debug', help='output debug lines', action='store_true')
    parser.add_argument('--deep', help='recurse into folders deeply with no limit', action='store_true')
    parser.add_argument('--full-probe', help='includes all probe data including streams info (video, audio, etc) from ffprobe when using --json', action='store_true')
    parser.add_argument('--json', help='output result in JSON', action='store_true')
    parser.add_argument('--print-extensions', help='print the list of extensions that are recognised as media files', action='store_true')
    parser.add_argument('--summary', help='output the summary only and exclude the line of details per file', action='store_true')
    args = parser.parse_args()
    logger.setLevel(logging.INFO)
    logger.formatter = logging.Formatter(fmt='%(message)s')
    handler_stdout = logging.StreamHandler(stream=sys.stdout)
    handler_stdout.setLevel(logging.INFO)
    logger.addHandler(handler_stdout)
    handler_stderr = logging.StreamHandler(stream=sys.stderr)
    handler_stderr.setLevel(logging.WARNING)
    logger.addHandler(handler_stderr)
    if args.debug:
        logger.setLevel(logging.DEBUG)
        handler_stderr.addFilter(lambda record: record.levelno >= logging.DEBUG)
        handler_stderr.setLevel(logging.DEBUG)
    elif args.summary or args.count or args.json:
        # Basically silence everything from logger module
        logger.removeHandler(handler_stdout)
        logger.removeHandler(handler_stderr)
        logger.setLevel(logging.CRITICAL)
    else:
        handler_stderr.addFilter(lambda record: record.levelno >= logging.WARNING)
    # Optional flags
    if args.print_extensions:
        if args.json:
            print( json.dumps(MEDIA_FILE_EXTENSIONS) )
        else:
            print( ', '.join(MEDIA_FILE_EXTENSIONS) )
        raise SystemExit
    # Parse items
    logger.debug(f"Input items: {args.items}")
    media_filepaths = list( get_media_filepaths(
        args.items,
        allow_all = args.allow_all,
        recurse = args.deep,
    ) )
    if len(media_filepaths) == 0:
        logger.info('No media files found. Check the path(s) or use --deep to recurse deeply into folders to find media files.')
        if args.json:
            output = json.dumps(
                {
                    'status': 'no_media_files_found',
                    'count_frames': 0,
                    'count_frames_by_framerate': {},
                    'files': [],
                },
                default = str,
            )
            print(output)
        raise SystemExit
    result = probe_filepaths(
        media_filepaths,
        include_probe = args.full_probe,
    )
    # Create output
    if args.json:
        if args.count:
            output = json.dumps( {
                'status': 'ok',
                'count_frames': result['count_frames'],
                'count_frames_by_framerate': result['count_frames_by_framerate']
            } )
            print(output)
        else:
            result.update({'status': 'ok'})
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
    
if __name__ == '__main__':
    main()
    

    

        

