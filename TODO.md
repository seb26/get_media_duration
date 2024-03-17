# TODO

- check that video frame count and file duration correspond
    - necessary? maybe just flag in error when they do

- add to macos finder extensions/quick actions
    - finder extensions - complicated
    - quick actions - perhaps need an Automator wrapper? maybe not
    - some examples: https://github.com/topics/quick-action

- handle drop frames - look at timecode library
    - how to determine this from ffprobe output?


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
