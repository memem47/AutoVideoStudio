# -*- coding: utf-8 -*-
"""VOICEVOX原稿読み上げ。標準ライブラリのみ使用。"""
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import wave

from config import load_config
CONFIG = load_config()
VOICEVOX_EXE = Path(CONFIG['voicevox_exe'])
API_BASE = CONFIG['voicevox_api'].rstrip('/')
SPEAKER_ID = CONFIG['speaker_id']
SCRIPT_DIR = Path(__file__).resolve().parent


def api_call(path, data=b'', content_type=None, timeout=120):
    headers = {}
    if content_type:
        headers['Content-Type'] = content_type
    req = urllib.request.Request(API_BASE + path, data=data, headers=headers, method='POST')
    with urllib.request.urlopen(req, timeout=timeout) as res:
        return res.read()


def engine_ready():
    try:
        with urllib.request.urlopen(API_BASE + '/version', timeout=2) as res:
            return res.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def ensure_engine():
    if engine_ready():
        return
    if not VOICEVOX_EXE.is_file():
        raise FileNotFoundError(f'VOICEVOX.exe が見つかりません: {VOICEVOX_EXE}')
    print('VOICEVOXを起動しています…')
    subprocess.Popen([str(VOICEVOX_EXE)], cwd=str(VOICEVOX_EXE.parent))
    for _ in range(90):
        if engine_ready():
            return
        time.sleep(1)
    raise RuntimeError('VOICEVOXのAPIに接続できません。VOICEVOXを起動し直してください。')


def chunks(text, limit=110):
    """長い原稿を日本語の句読点・改行で分割。"""
    pieces = re.split(r'(?<=[。！？!?])\s*|\n+', text.strip())
    result = []
    for piece in pieces:
        piece = piece.strip()
        if not piece:
            continue
        while len(piece) > limit:
            candidates = [m.end() for m in re.finditer(r'[、，,;； ]', piece[:limit])]
            cut = candidates[-1] if candidates and candidates[-1] > limit // 3 else limit
            result.append(piece[:cut].strip())
            piece = piece[cut:].strip()
        if piece:
            result.append(piece)
    return result


def synthesize(text):
    encoded = urllib.parse.urlencode({'text': text, 'speaker': SPEAKER_ID})
    query = api_call('/audio_query?' + encoded)
    # ニュースの読み上げ向けに少し落ち着いたテンポへ
    query_obj = json.loads(query.decode('utf-8'))
    query_obj['speedScale'] = CONFIG['speed_scale']
    query_obj['postPhonemeLength'] = 0.20
    query = json.dumps(query_obj, ensure_ascii=False).encode('utf-8')
    return api_call('/synthesis?speaker=' + str(SPEAKER_ID), query, 'application/json')


def combine_wavs(wav_blobs, out_path):
    with wave.open(str(out_path), 'wb') as output:
        expected = None
        for blob in wav_blobs:
            with wave.open(io.BytesIO(blob), 'rb') as source:
                props = (source.getnchannels(), source.getsampwidth(), source.getframerate(), source.getcomptype())
                if expected is None:
                    expected = props
                    output.setnchannels(props[0])
                    output.setsampwidth(props[1])
                    output.setframerate(props[2])
                    output.setcomptype(props[3], source.getcompname())
                elif props != expected:
                    raise RuntimeError('音声データの形式が途中で変わりました。')
                output.writeframes(source.readframes(source.getnframes()))


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else SCRIPT_DIR / 'sample.txt'
    if not path.is_file():
        raise FileNotFoundError(f'原稿が見つかりません: {path}')
    text = path.read_text(encoding='utf-8-sig').strip()
    if not text:
        raise ValueError('原稿が空です。')
    ensure_engine()
    segments = chunks(text)
    print(f'{len(segments)}区間の音声を生成します。')
    blobs = []
    for index, segment in enumerate(segments, 1):
        print(f'  {index}/{len(segments)}: {segment[:35]}')
        blobs.append(synthesize(segment))
    output_path = path.with_suffix('.wav')
    combine_wavs(blobs, output_path)
    print(f'\n完成: {output_path}')
    os.startfile(str(output_path))  # Windows既定プレイヤーで再生


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'\nエラー: {e}', file=sys.stderr)
        sys.exit(1)
