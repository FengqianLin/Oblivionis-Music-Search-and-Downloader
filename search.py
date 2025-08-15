from configure import *

def result_convert(playlist_data, source="netease"):
    """
    convert precise search result to common result
    """
    playlist_content = playlist_data.get("playlist", {})
    source_tracks = playlist_content.get("tracks", [])

    search_format_list = []
    for track in source_tracks:
        track_id = track.get("id")
        if track_id is None:
            continue

        artist_list = [artist.get("name") for artist in track.get("ar", []) if artist.get("name")]
        album_name = track.get("al", {}).get("name", "未知专辑")
        pic_id = track.get("al", []).get("pic")

        song_item = {
            "id": track_id,
            "name": track.get("name", "未知歌曲"),
            "artist": artist_list,
            "album": album_name,
            "pic_id": pic_id,
            "url_id": track_id,
            "lyric_id": track_id,
            "source": source,
        }
        search_format_list.append(song_item)

    return search_format_list

def search_worker(params, search_id):
    """
    search music thread
    """
    try:
        resp = session.get(BASE_URL, params=params, timeout=15).json()
        if isinstance(resp, dict):
            if "playlist" in resp:
                resp = result_convert(resp)
        search_queue.put(("success", resp, search_id))
    except requests.exceptions.Timeout:
        search_queue.put(("error", "搜索请求超时，请检查网络或稍后再试", search_id))
    except requests.exceptions.RequestException as e:
        search_queue.put(("error", f"搜索时网络错误: {e}", search_id))
    except Exception as e:
        search_queue.put(("error", f"网络错误或API无响应: {e}", search_id))

def pic_worker(params, pic_id):
    """
    get pic thread
    """
    try:
        resp = session.get(BASE_URL, params=params, timeout=10).json()
        url = resp.get("url")
        if url:
            img_data = session.get(url, timeout=10).content
            pic_queue.put(("success", img_data, pic_id))
        else:
            pic_queue.put(("error", "专辑封面未找到"))
    except requests.exceptions.Timeout:
        pic_queue.put(("error", "封面加载超时，请检查网络", pic_id))
    except requests.exceptions.RequestException as e:
        pic_queue.put(("error", f"封面加载网络错误: {e}", pic_id))
    except Exception as e:
        pic_queue.put(("error", f"图片加载失败: {e}", pic_id))