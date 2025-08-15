import queue
import requests
import os
import json

BASE_URL = "https://music-api.gdstudio.xyz/api.php"
CONFIG_FILE = "config.json"

ALL_SOURCES = [
    "netease", "tencent", "tidal", "spotify", "ytmusic", "qobuz", "joox",
    "deezer", "migu", "kugou", "kuwo", "ximalaya", "apple"
]
BITRATES = ["128", "192", "320", "740", "999"]

# multi-thread queue
search_queue = queue.Queue()
pic_queue = queue.Queue()
download_queue = queue.Queue()
# multi-thread cnt
search_id_counter = 0
download_tasks_total = 0
download_tasks_completed = 0
all_downloads_succeeded = True

# Session accelerates search
session = requests.Session()

# UI var
settings_window = None
FIXED_UI_FONT_SIZE = 10
UI_FONT_FAMILY = "Segoe UI"
MAX_COVER_SIZE = 210

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {
            "default_source": "netease",
            "default_search_type": "单曲/歌手搜索",
            "default_bitrate": "320",
            "download_lyrics": True,
            "default_music_path": "每次询问",
            "default_lyric_path": "每次询问",
        }

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)

def sanitize_filename(name):
    return "".join(c for c in name if c not in r'\/:*?"<>|').strip()