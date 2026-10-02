import os
from datetime import datetime
from typing import Optional
from pathlib import Path

import ffmpeg


FRAMERATE = '30'
VIDEO_CRF = '30'
AUDIO_BITRATE = '192k'
THREADS = '0'  # 0 = автоматически

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')

path = Path(OUTPUT_DIR)
path.mkdir(parents=True, exist_ok=True)

class ConversionError(RuntimeError):
    """Ошибка на стороне ffmpeg."""


def _timestamp() -> str:
    return datetime.now().strftime('%Y%m%d_%H%M%S_%f')


def _run(stream, output_path: str) -> str:
    try:
        ffmpeg.run(
            stream,
            overwrite_output=True,
            capture_stdout=True,
            capture_stderr=True,
        )
    except ffmpeg.Error as exc:
        stderr = exc.stderr.decode('utf-8', errors='replace') if exc.stderr else str(exc)
        raise ConversionError(stderr) from exc
    return os.path.abspath(output_path)


def stand(path: str, duration: int, audio_path: Optional[str] = None) -> str:
    audio_path = audio_path or os.path.abspath('output.ogg')
    if not os.path.isfile(audio_path):
        raise ConversionError(f'Аудиофайл не найден: {audio_path}')

    video = ffmpeg.input(path, framerate=30, loop=1, t=duration)
    audio = ffmpeg.input(audio_path, t=duration)
    output = os.path.join(OUTPUT_DIR, f'stand_{_timestamp()}.mp4')
    stream = ffmpeg.output(video, audio, output, **{
        'c:v': 'libx264',
        'crf': VIDEO_CRF,
        'r': FRAMERATE,
        'threads': THREADS,
        'c:a': 'aac',
        'b:a': AUDIO_BITRATE,
        'vf': (
            'fps=30, format=yuv420p, '
            'scale=w=1080:h=1920:force_original_aspect_ratio=1,'
            'pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black'
        ),
    })
    return _run(stream, output)


def bc(path: str, duration: int) -> str:
    video = ffmpeg.input(path, framerate=30, loop=1, t=duration)
    output = os.path.join(OUTPUT_DIR, f'stand_{_timestamp()}.mp4')
    stream = ffmpeg.output(video, output, **{
        'c:v': 'mpeg4',
        'tag:v': 'divx',
        'b:v': '4000K',
        'r': FRAMERATE,
        'vf': (
            'fps=30, format=yuv420p, '
            'scale=w=1080:h=1920:force_original_aspect_ratio=1,'
            'pad=1080:1920:(ow-iw)/2:(oh-ih)/2:white, transpose=2'
        ),
    })
    return _run(stream, output)


def tv(path: str) -> str:
    video = ffmpeg.input(path)
    output = os.path.join(OUTPUT_DIR, f'stand_{_timestamp()}.mp4')
    stream = ffmpeg.output(video, output, **{
        'c:v': 'libx264',
        'crf': VIDEO_CRF,
        'r': FRAMERATE,
        'threads': THREADS,
        'c:a': 'aac',
        'b:a': AUDIO_BITRATE,
        'vf': (
            'fps=30, format=yuv420p, '
            'scale=w=1920:h=1080:force_original_aspect_ratio=1,'
            'pad=1920:1080:(ow-iw)/2:(oh-ih)/2:white'
        ),
    })
    return _run(stream, output)


def stand_video(path: str) -> str:
    video = ffmpeg.input(path)
    output = os.path.join(OUTPUT_DIR, f'stand_{_timestamp()}.mp4')
    stream = ffmpeg.output(video, output, **{
        'c:v': 'libx264',
        'profile': 'main',
        'r': FRAMERATE,
        'c:a': 'aac',
        'b:a': AUDIO_BITRATE,
        'vf': (
            'fps=30, format=yuv420p, '
            'scale=w=1080:h=1920:force_original_aspect_ratio=1,'
            'pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black'
        ),
    })
    return _run(stream, output)


def bc_video(path: str) -> str:
    video = ffmpeg.input(path)
    output = os.path.join(OUTPUT_DIR, f'stand_{_timestamp()}.mp4')
    stream = ffmpeg.output(video, output, **{
        'c:v': 'mpeg4',
        'tag:v': 'divx',
        'b:v': '3000K',
        'r': FRAMERATE,
        'vf': (
            'fps=30, format=yuv420p, '
            'scale=w=1080:h=1920:force_original_aspect_ratio=1,'
            'pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black, transpose=2'
        ),
    })
    return _run(stream, output)


def tv_from_picture(path: str, duration: int) -> str:
    video = ffmpeg.input(path, framerate=30, loop=1, t=duration)
    output = os.path.join(OUTPUT_DIR, f'stand_{_timestamp()}.mp4')
    stream = ffmpeg.output(video, output, **{
        'c:v': 'libx264',
        'crf': VIDEO_CRF,
        'r': FRAMERATE,
        'threads': THREADS,
        'vf': (
            'fps=30, format=yuv420p, '
            'scale=w=1920:h=1080:force_original_aspect_ratio=1,'
            'pad=1920:1080:(ow-iw)/2:(oh-ih)/2:white'
        ),
    })
    return _run(stream, output)