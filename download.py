from configure import *
from mutagen.easyid3 import EasyID3  # For MP3 simple tags
from mutagen.id3 import ID3, APIC, USLT  # For MP3 advanced (artwork, lyrics)
from mutagen.flac import FLAC, Picture  # For FLAC
from mutagen import MutagenError

def download_worker(song_id, song_name, artist, album, source, pic_id, bitrate, save_dir_music, save_dir_lyric, semaphore):
    """
    download thread
    """
    semaphore.acquire()
    try:
        global all_downloads_succeeded
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
        lyric_file = None
        if save_dir_lyric:
            lyric_params = {"types": "lyric", "source": source, "id": song_id}
            lyric_data = session.get(BASE_URL, params=lyric_params, timeout=15).json()
            if "lyric" in lyric_data and lyric_data["lyric"]:
                lyric_file = os.path.join(save_dir_lyric, sanitize_filename(f"{song_name}.lrc"))
                with open(lyric_file, "w", encoding="utf-8") as f:
                    f.write(lyric_data["lyric"])

        # download album cover if pic_id exists
        cover_data = None
        if pic_id:
            pic_params = {"types": "pic", "source": source, "id": pic_id, "size": 500}
            pic_resp = session.get(BASE_URL, params=pic_params, timeout=15).json()
            pic_url = pic_resp.get("url")
            if pic_url:
                cover_resp = session.get(pic_url, timeout=15)
                cover_resp.raise_for_status()
                cover_data = cover_resp.content

        # embed metadata
        if ext == ".mp3":
            # Use EasyID3 for basic tags
            audio = EasyID3(music_file)
            audio['title'] = song_name
            audio['artist'] = artist if isinstance(artist, str) else ' / '.join(artist)  # Handle list or string
            audio['album'] = album
            audio.save()

            # Advanced: Embed artwork and lyrics using full ID3
            audio = ID3(music_file)
            if cover_data:
                audio.add(APIC(
                    encoding=3,  # UTF-8
                    mime='image/jpeg',  # Assume JPEG; adjust if needed
                    type=3,  # Cover (front)
                    desc='Cover',
                    data=cover_data
                ))
            if lyric_file and os.path.exists(lyric_file):
                with open(lyric_file, 'r', encoding='utf-8') as f:
                    lyric_text = f.read()
                plain_lyrics = '\n'.join(line.split(']', 1)[-1].strip() for line in lyric_text.splitlines() if ']' in line)
                audio.add(USLT(encoding=3, lang='eng', desc='Lyrics', text=plain_lyrics))
            audio.save()

        elif ext == ".flac":
            audio = FLAC(music_file)
            audio['title'] = song_name
            audio['artist'] = artist if isinstance(artist, str) else ' / '.join(artist)
            audio['album'] = album

            if cover_data:
                picture = Picture()
                picture.data = cover_data
                picture.type = 3  # Cover (front)
                picture.mime = 'image/jpeg'  # Assume JPEG
                picture.width = 500  # Placeholder; can extract actual
                picture.height = 500
                picture.depth = 24
                audio.add_picture(picture)

            if lyric_file and os.path.exists(lyric_file):
                with open(lyric_file, 'r', encoding='utf-8') as f:
                    lyric_text = f.read()
                plain_lyrics = '\n'.join(line.split(']', 1)[-1].strip() for line in lyric_text.splitlines() if ']' in line)
                audio['lyrics'] = plain_lyrics

            audio.save()

        download_queue.put(("success", song_name))

    except requests.exceptions.Timeout:
        all_downloads_succeeded = False
        download_queue.put(("error", f"'{song_name}' \n下载时连接超时"))
    except requests.exceptions.RequestException as e:
        all_downloads_succeeded = False
        download_queue.put(("error", f"'{song_name}' \n下载时发生网络错误: {e}"))
    except MutagenError as e:
        all_downloads_succeeded = False
        download_queue.put(("error", f"'{song_name}' \n元数据写入失败: {e}"))
    except Exception as e:
        all_downloads_succeeded = False
        download_queue.put(("error", f"'{song_name}' \n下载时发生未知错误: {e}"))

    finally:
        semaphore.release()