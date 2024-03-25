# get_media_duration

A simple utility to report frame count, frame rate and duration in HH:MM:SS:FF for a given media file or folders.

Uses [ffmpeg-python](https://github.com/kkroening/ffmpeg-python) to examine file metadata.

## Usage

```zsh
get_media_duration tests/sample_files/file_25p_30sec.mov 
```

Output:
There is two lines for each media file specified, and a summary recap at the end.
```
tests/sample_files/file_25p_30sec.mov
    Frames: 750 | Duration: 00:00:30:00 | FPS: 25 

    Files counted:       1
    Framerates found:    1 (25)
    Total framecount:    750
    Total duration:      00:00:30:00 @ 25 FPS
```

## Install

#### Compiled
1. Download binary for macOS ARM64 - GitHub > Releases
2. For macOS, remove any quarantine attributes and make executable:
```
cd /location/you/unzipped/to
xattr -c get_media_duration
chmod +x get_media_duration
./get_media_duration --help
```
3. Optional - For most non-tech savvy macOS users - store it locally and add to your path
```
makedirs ~/.local/bin
cp ./get_media_duration ~/.local/bin
echo $PATH=$PATH:$HOME/.local/bin
```
Then run it from anywhere you have a terminal. Helpful if you want to use Finder > Right-Click > Services > New Terminal Tab from Folder to put yourself right where you want to be in Terminal.

```
get_media_duration --help
```

<br />

#### Run as python module
You must have python >3.7 and pip >24. There is only a `pyproject.toml` provided, no setup.py or other.

```
# upgrade pip if you have not already
pip install --upgrade pip
pip install "git+https://github.com/seb26/get_media_duration.git"
python -m get_media_duration --help
```

<br />

#### Compile from source
1. Git clone
2. Create venv, use pyinstaller to compile
```bash
python -m venv .venv
.venv/bin/activate
pipenv install
pip install pyinstaller -U
pyinstaller get_media_duration.spec --noconfirm
```
3. Binary outputs to ```dist/get_media_duration```

Tests are based on pytest - see: `tests/`

## Documentation

### Media file extensions

By default, `get_media_duration` will only assess media files that have the following extensions. Extensions are case-insensitive (e.g. it will handle `.mp4` and `.MP4` fine).

This is to allow a useful assessment of actual media files, since `ffprobe` will provide metadata even for a variety of other types that aren't necessarily video.

```
MEDIA_FILE_EXTENSIONS = [ '264', '265', '266', '3g2', '3gp', 'amv', 'asf', 'avi', 'f4a', 'f4b', 'f4p', 'f4v', 'flv', 'flv', 'gifv', 'm4p', 'm4v', 'm4v', 'mkv', 'mng', 'mod', 'mov', 'mp2', 'mp4', 'mpe', 'mpeg', 'mpg', 'mpv', 'mxf', 'nsv', 'ogg', 'ogv', 'qt', 'rm', 'roq', 'rrc', 'svi', 'vob', 'webm', 'wmv', 'yuv' ]
```

### Folder items

You can pass a folder item and it will examine the immediate child files.

Use `--deep` to examine a folder deeply and examine all files at any level beneath that folder.

### Options

```
positional arguments:
  items               file or folder path(s) pointing to media files. For folders, will only
                      traverse only 1 level

options:
  -h, --help          show this help message and exit
  --version           show version
  --allow-all         assess files of all extensions
  --count             output only the frame count
  --debug             output debug lines
  --deep              recurse into folders deeply with no limit
  --full-probe        includes all probe data including streams info (video, audio, etc) 
                      from ffprobe when using --json
  --json              output result in JSON
  --print-extensions  print the list of extensions that are recognised as media files
  --summary           output the summary only and exclude the line of details per file
```

### Examples

JSON output.

```
get_media_duration tests/sample_files/file_25p_30sec.mov --json 
```
```json
{"count_files": 1, "count_files_skipped": 0, "count_framerates": {"25": 1}, "count_frames": 750, "count_frames_by_framerate": {"25": 750}, "files": [{"duration_timecode": "00:00:30:00", "filepath": "tests/sample_files/file_25p_30sec.mov", "fps": 25, "frame_count": 750}], "status": "ok"}
```

Count only.

```
get_media_duration tests/sample_files/ --count
```
```
750
```

<br />

JSON - count only.

```
get_media_duration tests/sample_files/file_25p_30sec.mov --json --count
```
```json
{"status": "ok", "count_frames": 750, "count_frames_by_framerate": {"25": 750}}
```

<br />

A folder item.

```
get_media_duration tests/sample_files/
```
```
tests/sample_files/file_25p_30sec.mov
    Frames: 750 | Duration: 00:00:30:00 | FPS: 25 
tests/sample_files/file_25p_120sec.mov
    Frames: 3,000 | Duration: 00:02:00:00 | FPS: 25 

    Files counted:       2
    Framerates found:    1 (25)
    Total framecount:    3,750
    Total duration:      00:02:30:00 @ 25 FPS
```

Same but with JSON output (beautified).

```
get_media_duration tests/sample_files/ --json 
```
```json
{
  "count_files": 2,
  "count_files_skipped": 0,
  "count_framerates": {
    "25": 2
  },
  "count_frames": 3750,
  "count_frames_by_framerate": {
    "25": 3750
  },
  "files": [
    {
      "duration_timecode": "00:00:30:00",
      "filepath": "tests/sample_files/file_25p_30sec.mov",
      "fps": 25,
      "frame_count": 750
    },
    {
      "duration_timecode": "00:02:00:00",
      "filepath": "tests/sample_files/file_25p_120sec.mov",
      "fps": 25,
      "frame_count": 3000
    }
  ],
  "status": "ok"
}
```

## License

Copyright (c) Sebastian Reategui, 2024. MIT License.