"""Load public defaults and optional machine-specific overrides."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent

def load_config():
    defaults = json.loads((ROOT / 'config.example.json').read_text(encoding='utf-8-sig'))
    local = ROOT / 'config.local.json'
    if local.is_file():
        defaults.update(json.loads(local.read_text(encoding='utf-8-sig')))
    return defaults
