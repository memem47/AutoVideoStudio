"""Combine ordered still images and WAV files into one H.264/AAC MP4."""
import argparse
import json
import math
from pathlib import Path
import shutil
import subprocess
import tempfile
import wave

from config import load_config
from subtitles import write_ass, write_srt

FPS = 30

def ffmpeg_path():
    configured = load_config()['ffmpeg_exe']
    exe = shutil.which(configured)
    if not exe:
        raise FileNotFoundError('FFmpeg not found. Install it and set ffmpeg_exe in config.local.json.')
    return exe

def make_video(pairs, output, scenes=None, subtitles=True):
    if not pairs:
        raise ValueError('No scenes')
    ffmpeg = ffmpeg_path()
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    def run(*args):
        subprocess.run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-y', *map(str, args)], check=True, cwd=str(folder))
    with tempfile.TemporaryDirectory(prefix='news_video_') as temp:
        folder = Path(temp)
        names = []
        for i, (image, audio) in enumerate(pairs, 1):
            with wave.open(str(audio), 'rb') as wav:
                duration = wav.getnframes() / wav.getframerate()
            if duration <= 0:
                raise ValueError(f'Empty audio: {audio}')
            duration = math.ceil(duration * FPS) / FPS
            clip = folder / f'{i:05}.mp4'
            print(f'Scene {i}/{len(pairs)}: {duration:.2f}s', flush=True)
            filters = 'scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1'
            if subtitles and scenes is not None:
                ass = folder / f'subtitle_{i:05}.ass'
                write_ass(scenes[i-1]['text'], duration, ass)
                filters += f',ass={ass.name}'
            run('-loop', '1', '-framerate', FPS, '-i', image, '-i', audio,
                '-vf', filters,
                '-af', 'apad', '-t', f'{duration:.9f}', '-map', '0:v:0', '-map', '1:a:0',
                '-c:v', 'libx264', '-preset', 'fast', '-crf', '20', '-pix_fmt', 'yuv420p',
                '-r', FPS, '-c:a', 'aac', '-ar', '48000', '-ac', '1', '-b:a', '128k', clip)
            names.append(clip.name)
        listing = folder / 'concat.txt'
        listing.write_text(''.join(f"file '{name}'\n" for name in names), encoding='ascii')
        run('-f', 'concat', '-safe', '0', '-i', listing, '-c', 'copy', '-movflags', '+faststart', output)
    print(f'Finished: {output}')

def main():
    p = argparse.ArgumentParser()
    p.add_argument('project', type=Path)
    p.add_argument('--output', type=Path)
    p.add_argument('--no-subtitles', action='store_true', help='Disable burned-in captions')
    args = p.parse_args()
    project = args.project.resolve()
    scenes = json.loads((project / 'scenes.json').read_text(encoding='utf-8-sig'))
    pairs = [(project / s['image'], project / 'audio' / f'{i:02}.wav') for i,s in enumerate(scenes,1)]
    output = args.output or project / 'output.mp4'
    if not args.no_subtitles:
        write_srt(scenes, [a for _, a in pairs], Path(output).with_suffix('.srt'), fps=FPS)
    make_video(pairs, output, scenes=scenes, subtitles=not args.no_subtitles)

if __name__ == '__main__':
    main()
