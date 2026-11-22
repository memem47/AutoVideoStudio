"""Generate SRT subtitles and FFmpeg ASS overlays from narration and WAV durations."""
import math
import re
import wave
from pathlib import Path

def audio_duration(path):
    with wave.open(str(path), 'rb') as w:
        return w.getnframes() / w.getframerate()

def split_text(text, limit=23):
    pieces = re.split(r'(?<=[。！？!?])\s*|(?<=[、，,])\s*|\n+', text.strip())
    out = []
    for piece in pieces:
        piece = piece.strip()
        while len(piece) > limit:
            cut = max(piece.rfind(' ', 0, limit + 1), piece.rfind('　', 0, limit + 1))
            if cut < limit // 2:
                cut = limit
            out.append(piece[:cut].strip())
            piece = piece[cut:].strip()
        if piece:
            out.append(piece)
    return out

def scene_cues(text, duration):
    parts = split_text(text)
    if not parts or duration <= 0:
        return []
    weights = [max(1, len(p.replace(' ', ''))) for p in parts]
    total = sum(weights)
    start = 0.0
    result = []
    for i, (part, weight) in enumerate(zip(parts, weights)):
        end = duration if i == len(parts) - 1 else start + duration * weight / total
        result.append((start, end, part))
        start = end
    return result

def timestamp(seconds):
    millis = round(seconds * 1000)
    hours, rem = divmod(millis, 3600000)
    minutes, rem = divmod(rem, 60000)
    secs, ms = divmod(rem, 1000)
    return f'{hours:02}:{minutes:02}:{secs:02},{ms:03}'

def write_srt(scenes, audio_paths, output, fps=30):
    clock = 0.0
    lines = []
    index = 1
    for scene, path in zip(scenes, audio_paths):
        duration = audio_duration(path)
        for start, end, caption in scene_cues(scene['text'], duration):
            lines += [str(index), f'{timestamp(clock+start)} --> {timestamp(clock+end)}', caption, '']
            index += 1
        clock += math.ceil(duration * fps) / fps
    output = Path(output)
    output.write_text('\n'.join(lines), encoding='utf-8-sig')
    return output

def ass_time(seconds):
    cs = round(seconds * 100)
    h, rem = divmod(cs, 360000)
    m, rem = divmod(rem, 6000)
    s, c = divmod(rem, 100)
    return f'{h}:{m:02}:{s:02}.{c:02}'

def write_ass(text, duration, output, font='Meiryo'):
    header = ("[Script Info]\nScriptType: v4.00+\nPlayResX: 1280\nPlayResY: 720\n"
              "WrapStyle: 2\nScaledBorderAndShadow: yes\n\n[V4+ Styles]\n"
              "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
              f"Style: Default,{font},45,&H00FFFFFF,&H00FFFFFF,&H00171717,&H80000000,-1,0,0,0,100,100,0,0,1,3,1,2,60,60,40,1\n\n"
              "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    events = []
    for start, end, caption in scene_cues(text, duration):
        safe = caption.replace('\\', '\\\\').replace('{', '\\{').replace('}', '\\}').replace('\n', '\\N')
        events.append(f'Dialogue: 0,{ass_time(start)},{ass_time(end)},Default,,0,0,0,,{safe}')
    Path(output).write_text(header + '\n'.join(events) + '\n', encoding='utf-8-sig')
