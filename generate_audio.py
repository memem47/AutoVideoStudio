"""Generate one VOICEVOX WAV per scene."""
import argparse
import json
from pathlib import Path
import voicevox

def main():
    p = argparse.ArgumentParser()
    p.add_argument('project', type=Path)
    p.add_argument('--speaker', type=int, default=voicevox.SPEAKER_ID)
    args = p.parse_args()
    project = args.project.resolve()
    scenes = json.loads((project / 'scenes.json').read_text(encoding='utf-8-sig'))
    if not scenes or any(not s['text'].strip() for s in scenes):
        raise ValueError('Empty scene or narration')
    voicevox.SPEAKER_ID = args.speaker
    voicevox.ensure_engine()
    (project / 'audio').mkdir(exist_ok=True)
    for i, scene in enumerate(scenes, 1):
        print(f'Audio {i}/{len(scenes)}: {scene["text"]}', flush=True)
        blobs = [voicevox.synthesize(t) for t in voicevox.chunks(scene['text'])]
        voicevox.combine_wavs(blobs, project / 'audio' / f'{i:02}.wav')

if __name__ == '__main__':
    main()
