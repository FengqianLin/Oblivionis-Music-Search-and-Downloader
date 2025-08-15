from configure import *

def search_worker(params, search_id):
    """
    search music thread
    """
    try:
        resp = session.get(BASE_URL, params=params, timeout=15).json()
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