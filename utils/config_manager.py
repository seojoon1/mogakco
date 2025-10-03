import os
import json
import asyncio

CONFIG_FILE = "config.json"
config_lock = asyncio.Lock()

def load_config():
    """설정 파일을 로드합니다."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_config(config):
    """설정 파일을 저장합니다."""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
