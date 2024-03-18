# TODO

## bugs

## features/compatibility:

- check that video frame count and file duration correspond
    - necessary? maybe just flag in error when they do

- add to macos finder extensions/quick actions
    - finder extensions - complicated
    - quick actions - perhaps need an Automator wrapper? maybe not
    - some examples: https://github.com/topics/quick-action

- handle drop frames - look at timecode library
    - how to determine this from ffprobe output?

- test 23.976 clips some more - see if they are showing up as 24 - they might not

- handle VFR/iPhone footage better
    - currently VFR clips can return a frame rate of as stupid as 30030000
    - maybe use a different frame rate attribute from ffprobe

- handle ARRI-created MXF
    ```
    /Users/seb/Downloads/Resolve18-5_mixed_footage_logC3_and_logC4_ARRI_REVEAL_ColorScience_NonColormanaged.dra/MediaFiles/ARRI_Helen_John_ARRIRAW_MXF_1frame/ARRI_Helen_John_ALEXA_35_ARRIRAW_frame.mxf
    Skipped. Exception while getting metadata about this file - 'nb_frames'
    ```
    - ffprobe says:
[mxf @ 0x1208145a0] Stream #0: not enough frames to estimate rate; consider increasing probesize
    - 

- when printing framerate summary, order by FPS


# PLAN

Input
- Take in input file as single
- Take in folder
    - Create a macOS Finder Service or Quick action


- Single standalone CLI noninteractive script, with args

Then:
- Get duration of video file(s)
- Present as:
    - Total # files
    - Frame count: 10,000
    - FPS: 25
    - Duration: 00:06:40:00
