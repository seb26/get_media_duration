import pytest
from pathlib import Path, PosixPath

from get_media_duration import (
    MediaFile, 
    display_frames_to_tc,
    get_media_filepaths,
    has_media_file_extension,
    probe_filepaths,
    summary_output,
)
from timecode import Timecode

@pytest.mark.parametrize(
    'args,kwargs,expected_result', [
        [['23.976'], {'frames': 10000}, '00:06:56:16'],
        [['24'], {'frames': 10000}, '00:06:56:16'],
        [['29.97'], {'frames': 10000}, '00:05:33;20'], #df
        [['29.97'], {'frames': 10000, 'force_non_drop_frame': True}, '00:05:33:10'],
        [['30'], {'frames': 10000}, '00:05:33:10'],
        [['50'], {'frames': 10000}, '00:03:20:00'],
        [['50'], {'frames': 10000}, '00:03:20:00'],
        [['59.94'], {'frames': 10000}, '00:02:46;48'], #df
        [['59.94'], {'frames': 10000, 'force_non_drop_frame': True}, '00:02:46:40'],
        [['60'], {'frames': 10000}, '00:02:46:40'],
    ]
)
def test_display_frames_to_tc(args, kwargs, expected_result):
    """Display Frames->TC should match these precomputed durations"""
    assert display_frames_to_tc(*args, **kwargs) == expected_result

@pytest.mark.parametrize(
    'args,kwargs,expected_result', [
        # File
        [['tests/sample_files/file_25p_30sec.mov'], {}, [Path('tests/sample_files/file_25p_30sec.mov')]],
        # Multiple files
        [[['tests/sample_files/file_25p_120sec.mov', 'tests/sample_files/file_25p_30sec.mov']], {}, [Path('tests/sample_files/file_25p_120sec.mov'), Path('tests/sample_files/file_25p_30sec.mov')]],
        # Folder with child files
        [['tests/sample_files'], {}, [Path('tests/sample_files/file_25p_30sec.mov'), Path('tests/sample_files/file_25p_120sec.mov')]],
        # Folder with no immediate file children
        [['tests'], {}, []],
        # Non-media files
        [['tests/sample_files/document.pdf'], {}, []],
        [['tests/sample_files/document.pdf'], {'allow_all': True}, [Path('tests/sample_files/document.pdf')]],
    ]
)
def test_get_media_filepaths(args, kwargs, expected_result):
    assert list(get_media_filepaths(*args, **kwargs)) == expected_result

sample_parameters = [
    [
        [
            [
                PosixPath('tests/sample_files/file_25p_30sec.mov'),
                PosixPath('tests/sample_files/file_25p_120sec.mov'),
            ],
        ],
        {},
        {
            'count_files_skipped': 0,
            'count_files': 2,
            'count_framerates': { 25: 2 },
            'count_frames': 3750,
            'count_frames_by_framerate': {25: 3750},
            'files': [
                {
                    'duration_timecode': '00:00:30:00',
                    'filepath': PosixPath('tests/sample_files/file_25p_30sec.mov'),
                    'fps': 25,
                    'frame_count': 750
                },
                {   
                    'duration_timecode': '00:02:00:00',
                    'filepath': PosixPath('tests/sample_files/file_25p_120sec.mov'),
                    'fps': 25,
                    'frame_count': 3000
                },
            ],
        },
    ]
]

def probe_filepaths_attribute_check(attribute, args, kwargs, expected_result):
    return probe_filepaths(*args, **kwargs).get(attribute, True) == expected_result.get(attribute, False)

@pytest.mark.parametrize('args,kwargs,expected_result', sample_parameters)
def test_filepaths_attribute_check__count_files_skipped(args, kwargs, expected_result):
    assert probe_filepaths_attribute_check('count_files_skipped', args, kwargs, expected_result)

@pytest.mark.parametrize('args,kwargs,expected_result', sample_parameters)
def test_filepaths_attribute_check__count_files(args, kwargs, expected_result):
    assert probe_filepaths_attribute_check('count_files', args, kwargs, expected_result)

@pytest.mark.parametrize('args,kwargs,expected_result', sample_parameters)
def test_filepaths_attribute_check__count_frames(args, kwargs, expected_result):
    assert probe_filepaths_attribute_check('count_frames', args, kwargs, expected_result)

@pytest.mark.parametrize('args,kwargs,expected_result', sample_parameters)
def test_filepaths_attribute_check__count_framerates(args, kwargs, expected_result):
    assert probe_filepaths_attribute_check('count_framerates', args, kwargs, expected_result)

@pytest.mark.parametrize('args,kwargs,expected_result', sample_parameters)
def test_filepaths_attribute_check__count_frames_by_framerate(args, kwargs, expected_result):
    assert probe_filepaths_attribute_check('count_frames_by_framerate', args, kwargs, expected_result)

@pytest.mark.parametrize('args,kwargs,expected_result', sample_parameters)
def test_filepaths_attribute_check__files(args, kwargs, expected_result):
    result = probe_filepaths(*args, **kwargs)
    assert result['files'][0].get('filepath', True) == expected_result['files'][0].get('filepath', False)
    assert result['files'][0].get('fps', True) == expected_result['files'][0].get('fps', False)
    assert result['files'][0].get('frame_count', True) == expected_result['files'][0].get('frame_count', False)
    assert result['files'][0].get('duration_timecode', True) == expected_result['files'][0].get('duration_timecode', False)

