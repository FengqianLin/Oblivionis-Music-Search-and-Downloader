import re
from collections import defaultdict
from mutagen.easyid3 import EasyID3  # For MP3 simple tags
from mutagen.id3 import ID3, APIC, USLT  # For MP3 advanced (artwork, lyrics)
from mutagen.flac import FLAC, Picture  # For FLAC
from mutagen import MutagenError

from configure import *


def merge_lyrics(original_lrc, translated_lrc):
    """
    Merge original and translated lyrics
    """
    lyric_dict = defaultdict(list)

    # Capture timestamp and text. Handles both [mm:ss.xx] and [mm:ss:xx]
    lrc_line_regex = re.compile(r'(\[\d{2}:\d{2}[.:]\d{2,3}\])(.*)')

    # Process original lyrics
    for line in original_lrc.splitlines():
        match = lrc_line_regex.match(line)
        if match:
            timestamp, text = match.groups()
            lyric_dict[timestamp].append(text.strip())

    # Process translated lyrics
    for line in translated_lrc.splitlines():
        match = lrc_line_regex.match(line)
        if match:
            timestamp, text = match.groups()

            if timestamp in lyric_dict:
                lyric_dict[timestamp].append(text.strip())
            else:
                lyric_dict[timestamp].insert(0, "")
                lyric_dict[timestamp].append(text.strip())

    # rebuild LRC
    merged_lines = []
    for timestamp, texts in sorted(lyric_dict.items()):
        if len(texts) == 1:
            # only one LRC
            merged_lines.append(f"{timestamp}{texts[0]}")
        elif len(texts) > 1:
            # bilingual LRC
            merged_lines.append(f"{timestamp}{texts[0]}")
            merged_lines.append(f"{timestamp}{texts[1]}")

    return "\n".join(merged_lines)


def download_worker(thread_str, song_id, song_name, artist, album, source, pic_id, bitrate, cover_size, lyric_mode, save_dir_music, save_dir_lyric, semaphore):
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
        if thread_str and (thread_str[-1] == "!" or thread_str[-1] == "+"):
                music_file = os.path.join(save_dir_music, sanitize_filename(f"{thread_str[:-1]}.{song_name}{ext}"))
        else:
            music_file = os.path.join(save_dir_music, sanitize_filename(f"{song_name}{ext}"))

        with session.get(music_url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(music_file, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        # lyric handling
        final_lyric_content = ""

        if lyric_mode != "不下载歌词":
            lyric_params = {"types": "lyric", "source": source, "id": song_id}
            lyric_data = session.get(BASE_URL, params=lyric_params, timeout=15).json()

            original_lyric = lyric_data.get("lyric")
            translated_lyric = lyric_data.get("tlyric")

            if original_lyric and translated_lyric:
                final_lyric_content = merge_lyrics(original_lyric, translated_lyric)
            elif original_lyric:
                final_lyric_content = original_lyric
            elif translated_lyric:
                final_lyric_content = translated_lyric

            # 保存 .lrc 文件（模式 3 & 4）
            if final_lyric_content and lyric_mode in ["只下载.lrc歌词文件", "同时内嵌歌词并下载.lrc歌词文件"] and save_dir_lyric:
                if thread_str and (thread_str[-1] == "!" or thread_str[-1] == "+"):
                        lyric_file = os.path.join(save_dir_lyric, sanitize_filename(f"{thread_str[:-1]}.{song_name}.lrc"))
                else:
                    lyric_file = os.path.join(save_dir_lyric, sanitize_filename(f"{song_name}.lrc"))
                with open(lyric_file, "w", encoding="utf-8") as f:
                    f.write(final_lyric_content)

        # download album cover with custom size
        cover_data = None
        if pic_id:
            pic_params = {"types": "pic", "source": source, "id": pic_id, "size": cover_size}
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
            if thread_str and (thread_str[-1] == "." or thread_str[-1] == "+"):
                audio['tracknumber'] = thread_str[:-1]
            audio.save()

            # Advanced: Embed artwork and lyrics using full ID3
            audio = ID3(music_file)
            if cover_data:
                audio.add(APIC(
                    encoding=3,  # UTF-8
                    mime='image/jpeg',  # Assume JPEG
                    type=3,  # Cover (front)
                    desc='Cover',
                    data=cover_data
                ))
            if final_lyric_content and lyric_mode in ["只内嵌歌词", "同时内嵌歌词并下载.lrc歌词文件"]:
                # plain_lyrics = '\n'.join(line.split(']', 1)[-1].strip() for line in final_lyric_content.splitlines() if ']' in line)
                # audio.add(USLT(encoding=3, lang='eng', desc='Lyrics', text=plain_lyrics))
                audio.add(USLT(encoding=3, desc='Lyrics', text=final_lyric_content))
            audio.save()

        elif ext == ".flac":
            audio = FLAC(music_file)
            audio['title'] = song_name
            audio['artist'] = artist if isinstance(artist, str) else ' / '.join(artist)
            audio['album'] = album
            if thread_str and (thread_str[-1] == "." or thread_str[-1] == "+"):
                audio['tracknumber'] = thread_str[:-1]

            if cover_data:
                picture = Picture()
                picture.data = cover_data
                picture.type = 3  # Cover (front)
                picture.mime = 'image/jpeg'  # Assume JPEG
                picture.width = cover_size
                picture.height = cover_size
                picture.depth = 24
                audio.add_picture(picture)

            if final_lyric_content and lyric_mode in ["只内嵌歌词", "同时内嵌歌词并下载.lrc歌词文件"]:
                # plain_lyrics = '\n'.join(line.split(']', 1)[-1].strip() for line in final_lyric_content.splitlines() if ']' in line)
                # audio['lyrics'] = plain_lyrics
                audio['lyrics'] = final_lyric_content

            audio.save()

        download_queue.put(("success", song_name))

    except requests.exceptions.Timeout:
        all_downloads_succeeded = False
        retry_args = (thread_str, song_id, song_name, artist, album, source, pic_id, bitrate, cover_size, lyric_mode,
                      save_dir_music, save_dir_lyric, semaphore)

        download_queue.put(("error", (f"'{song_name}' \n下载时连接超时", retry_args)))
    except requests.exceptions.RequestException as e:
        all_downloads_succeeded = False
        retry_args = (thread_str, song_id, song_name, artist, album, source, pic_id, bitrate, cover_size, lyric_mode,
                      save_dir_music, save_dir_lyric, semaphore)

        download_queue.put(("error", (f"'{song_name}' \n下载时发生网络错误: {e}", retry_args)))
    except MutagenError as e:
        all_downloads_succeeded = False
        retry_args = (thread_str, song_id, song_name, artist, album, source, pic_id, bitrate, cover_size, lyric_mode,
                      save_dir_music, save_dir_lyric, semaphore)

        download_queue.put(("error", (f"'{song_name}' \n元数据写入失败: {e}", retry_args)))
    except Exception as e:
        all_downloads_succeeded = False
        retry_args = (thread_str, song_id, song_name, artist, album, source, pic_id, bitrate, cover_size, lyric_mode,
                      save_dir_music, save_dir_lyric, semaphore)

        download_queue.put(("error", (f"'{song_name}' \n下载时发生未知错误: {e}", retry_args)))

    finally:
        semaphore.release()
