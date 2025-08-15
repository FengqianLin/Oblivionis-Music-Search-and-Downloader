from configure import *

def download_worker(song_id, song_name, source, bitrate, save_dir_music, save_dir_lyric):
    """
    download thread
    """
    global all_downloads_succeeded
    try:
        url_params = {
            "types": "url",
            "source": source,
            "id": song_id,
            "br": bitrate
        }
        music_data = session.get(BASE_URL, params=url_params, timeout=15).json()
        music_url = music_data.get("url")
        if not music_url:
            download_queue.put(("error", f"未能获取歌曲\n '{song_name}' \n的下载链接"))
            all_downloads_succeeded = False
            return

        # download music
        br = music_data.get("br", 0)
        ext = ".flac" if isinstance(br, (int, float)) and br >= 740 else ".mp3"
        music_file = os.path.join(save_dir_music, sanitize_filename(f"{song_name}{ext}"))

        with session.get(music_url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(music_file, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        # download lyric
        if save_dir_lyric:
            lyric_params = {"types": "lyric", "source": source, "id": song_id}
            lyric_data = session.get(BASE_URL, params=lyric_params, timeout=15).json()
            if "lyric" in lyric_data and lyric_data["lyric"]:
                lyric_file = os.path.join(save_dir_lyric, sanitize_filename(f"{song_name}.lrc"))
                with open(lyric_file, "w", encoding="utf-8") as f:
                    f.write(lyric_data["lyric"])

        download_queue.put(("success", song_name))

    except requests.exceptions.Timeout:
        all_downloads_succeeded = False
        download_queue.put(("error", f"下载\n '{song_name}' \n时连接超时"))
    except requests.exceptions.RequestException as e:
        all_downloads_succeeded = False
        download_queue.put(("error", f"下载\n '{song_name}' \n时发生网络错误: {e}"))
    except Exception as e:
        all_downloads_succeeded = False
        download_queue.put(("error", f"下载\n '{song_name}' \n时发生未知错误: {e}"))