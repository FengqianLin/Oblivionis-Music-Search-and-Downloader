import queue
import requests
import os
import json
import sys

def get_user_data_dir():
    if sys.platform.startswith("win"):
        base_dir = os.getenv("APPDATA")
    elif sys.platform.startswith("darwin"):
        base_dir = os.path.expanduser("~/Library/Application Support")
    else:
        base_dir = os.path.expanduser("~/.config")

    app_dir = os.path.join(base_dir, "Oblivionis")
    os.makedirs(app_dir, exist_ok=True)
    return app_dir

CONFIG_FILE = os.path.join(get_user_data_dir(), "config.json")

BASE_URL = "https://music-api.gdstudio.xyz/api.php"

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

# Default configuration with new lyric mode
DEFAULT_CONFIG = {
    "default_source": "netease",
    "default_search_type": "单曲/歌手搜索",
    "default_bitrate": "320",
    "download_lyrics": True,
    "max_downloads": 3,
    "default_music_path": "每次询问",
    "default_lyric_path": "每次询问",
    "album_cover_size": 500,
    "embed_lyrics_only": False,
    # New lyric mode key
    "lyric_mode": "同时内嵌歌词并下载.lrc歌词文件"
}

def load_config():
    """Load configuration from file, merging with defaults and handling old flags."""
    config = DEFAULT_CONFIG.copy()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                user_config = json.load(f)
                if isinstance(user_config, dict):
                    config.update(user_config)
        except (IOError, json.JSONDecodeError):
            pass

    # Backwards compatibility: convert old boolean flags to new string mode
    if "download_lyrics" in config and "embed_lyrics_only" in config:
        download_lyrics = config.pop("download_lyrics")
        embed_only = config.pop("embed_lyrics_only")

        if not download_lyrics:
            config["lyric_mode"] = "不下载歌词"
        elif embed_only:
            config["lyric_mode"] = "只内嵌歌词"
        else:
            # This covers the old default of downloading both embedded and .lrc files
            config["lyric_mode"] = "同时内嵌歌词并下载.lrc歌词文件"

    return config

def save_config(cfg):
    """Save configuration to file."""
    # Remove old flags before saving to ensure clean config file
    cfg.pop("download_lyrics", None)
    cfg.pop("embed_lyrics_only", None)
    
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)

def sanitize_filename(name):
    return "".join(c for c in name if c not in r'\/:*?"<>|').strip()