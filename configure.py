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
DOWNLOAD_INTERVAL = 5.1

# 线程/队列
search_queue = queue.Queue()
pic_queue    = queue.Queue()
download_queue = queue.Queue()
task_queue = queue.Queue()

search_id_counter = 0
download_tasks_total = 0
download_tasks_completed = 0
all_downloads_succeeded = True

session = requests.Session()

# UI 常量
settings_window = None
FIXED_UI_FONT_SIZE = 10
UI_FONT_FAMILY = "Segoe UI"
MAX_COVER_SIZE = 210

# 默认配置（只剩 lyric_mode）
DEFAULT_CONFIG = {
    "default_source": "netease",
    "default_search_type": "单曲/歌手搜索",
    "default_bitrate": "320",
    "default_search_count": 20,
    "lyric_mode": "同时内嵌歌词并下载.lrc歌词文件",
    "max_downloads": 3,
    "record_number_type": "不编号",
    "default_music_path": "每次询问",
    "default_lyric_path": "每次询问",
    "album_cover_size": 500
}

def load_config():
    """读取配置；不存在就用默认"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                if isinstance(cfg, dict):
                    return {**DEFAULT_CONFIG, **cfg}
        except (IOError, json.JSONDecodeError):
            pass
    return DEFAULT_CONFIG.copy()

def save_config(cfg):
    """保存配置；无需再处理旧 key"""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)

def sanitize_filename(name):
    return "".join(c for c in name if c not in r'\/:*?"<>|').strip()