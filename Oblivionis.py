import requests
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os, json
from io import BytesIO
import webbrowser
import threading
import queue
import pickle

BASE_URL = "https://music-api.gdstudio.xyz/api.php"
CONFIG_FILE = "config.json"
COOKIE_FILE = 'session_cookies.pkl'

ALL_SOURCES = [
    "netease", "tencent", "tidal", "spotify", "ytmusic", "qobuz", "joox",
    "deezer", "migu", "kugou", "kuwo", "ximalaya", "apple"
]
BITRATES = ["128", "192", "320", "740", "999"]

current_page = 1
current_keyword = ""
current_source = "netease"
current_search_type = "单曲/歌手搜索"

# multi-thread var
search_queue = queue.Queue()
pic_queue = queue.Queue()
search_id_counter = 0

# Session accelerates search
session = requests.Session()

# ---------------- 配置管理 ----------------
def load_config():
    """
    read from config.json
    :return:
    """
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {
            "default_source": "netease",
            "default_search_type": "单曲/歌手搜索",
            "default_bitrate": "320",
            "default_music_path": "每次询问",
            "default_lyric_path": "每次询问"
        }

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)

config = load_config()

def sanitize_filename(name):
    return "".join(c for c in name if c not in r'\/:*?"<>|').strip()

# ------------- cookie -------------
def load_cookies():
    if os.path.exists(COOKIE_FILE):
        try:
            with open(COOKIE_FILE, 'rb') as f:
                session.cookies.update(pickle.load(f))
        except Exception as e:
            messagebox.showerror("cookie error: ", str(e))

def on_closing():
    try:
        with open(COOKIE_FILE, 'wb') as f:
            pickle.dump(session.cookies, f)
    except Exception as e:
        messagebox.showerror("cookie error: ", str(e))
    finally:
        session.close()
        root.destroy()

load_cookies()

# ---------------- 搜索功能 ----------------
def _search_worker(params, search_id):
    """
    download music thread
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

def _update_song_list(resp):
    """
    update song_list after search
    """
    song_list.delete(*song_list.get_children())
    if not resp:
        messagebox.showinfo("提示", "未找到相关结果")
        return

    for song in resp:
        song_list.insert("", tk.END, values=(
            song["id"], song["name"], song["artist"], song["album"], song["source"], song.get("pic_id", "")
        ))
    song_list.yview_moveto(0)

def _pic_worker(params, pic_id):
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

def _update_album_cover(img_data):
    """
    update album_label after search
    """
    try:
        img = Image.open(BytesIO(img_data))
        max_width, max_height = 250, 250
        img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        album_label.config(image=photo, text="")
        album_label.image = photo
    except Exception:
        album_label.config(image=None, text="封面加载失败")

def process_queue():
    """
    handle both search queue and pic queue
    """
    global search_id_counter
    # handle searching
    try:
        status, data, search_id = search_queue.get_nowait()

        if search_id == search_id_counter:
            if status == "success":
                _update_song_list(data)
            elif status == "error":
                song_list.delete(*song_list.get_children())
                messagebox.showerror("搜索歌曲错误", data)
    except queue.Empty:
        pass

    # handle pic
    try:
        status, data, pic_id = pic_queue.get_nowait()
        if status == "success":
            _update_album_cover(data)
        elif status == "error":
            messagebox.showerror("搜索封面错误", data)
    except queue.Empty:
        pass

    finally:
        root.after(100, process_queue)

def search_music(keyword, source, search_type, page=1):
    """
    create a searching thread
    """
    global current_keyword, current_source, current_page, current_search_type, search_id_counter

    # clear song_list for upcoming result
    song_list.delete(*song_list.get_children())
    song_list.insert("", tk.END, values=("", "正在搜索，请稍候...", "", "", "", ""))
    root.update_idletasks()

    api_source = f"{source}_album" if search_type == "专辑搜索" else source

    current_keyword = keyword
    current_source = source
    current_search_type = search_type
    current_page = page

    params = {
        "types": "search",
        "source": api_source,
        "name": keyword,
        "count": config.get("default_search_count", 20),
        "pages": page
    }
    # create thread
    search_id_counter += 1
    thread = threading.Thread(target=_search_worker, args=(params, search_id_counter), daemon=True)
    thread.start()

def handle_new_search():
    keyword = entry_keyword.get().strip()
    if not keyword:
        messagebox.showwarning("警告", "请输入搜索内容")
        return
    source = combo_source.get()
    search_type = combo_search_type.get()
    print("ok")
    search_music(keyword, source, search_type, page=1)

# ---------------- 下载功能 ----------------
def download_music(song_id, song_name, source, save_dir_music, save_dir_lyric):
    try:
        url_params = {
            "types": "url",
            "source": source,
            "id": song_id,
            "br": config.get("default_bitrate", "320")
        }
        music_data = session.get(BASE_URL, params=url_params).json()
        music_url = music_data.get("url")
        if music_url:
            # 判断是否为无损
            br = music_data.get("br", 0)
            ext = ".flac" if br >= 740 else ".mp3"

            music_file = os.path.join(save_dir_music,
                                      sanitize_filename(f"{song_name}{ext}"))
            if os.path.exists(music_file):
                os.remove(music_file)

            with session.get(music_url, stream=True) as r:
                total_length = int(r.headers.get('content-length', 0))
                dl = 0
                with open(music_file, "wb") as f:
                    for chunk in r.iter_content(1024):
                        if chunk:
                            f.write(chunk)
                            dl += len(chunk)
                            if total_length > 0:
                                progress_var.set(int(dl * 100 / total_length))
                                root.update_idletasks()
        else:
            messagebox.showwarning("下载提示", f"未能获取歌曲 '{song_name}' 的下载链接")
            return False

        lyric_params = {
            "types": "lyric",
            "source": source,
            "id": song_id
        }
        lyric_data = session.get(BASE_URL, params=lyric_params).json()
        if "lyric" in lyric_data:
            lyric_file = os.path.join(save_dir_lyric, sanitize_filename(f"{song_name}.lrc"))
            with open(lyric_file, "w", encoding="utf-8") as f:
                f.write(lyric_data["lyric"])
        return True

    except requests.exceptions.Timeout:
        messagebox.showerror("下载超时", f"下载歌曲 '{song_name}' 时连接超时，请检查网络后重试")
        progress_var.set(0)
        return False
    except requests.exceptions.RequestException as e:
        messagebox.showerror("下载错误", f"下载歌曲 '{song_name}' 时发生网络错误: {e}")
        progress_var.set(0)
        return False

def download_selected():
    items = song_list.selection()
    if not items:
        messagebox.showwarning("警告", "请选择要下载的歌曲")
        return

    if config["default_music_path"] == "每次询问":
        save_dir_music = filedialog.askdirectory(title="选择音乐保存位置", parent=root)
        if not save_dir_music:
            return
    else:
        save_dir_music = config["default_music_path"]

    if config["default_lyric_path"] == "每次询问":
        save_dir_lyric = filedialog.askdirectory(title="选择歌词保存位置", parent=root)
        if not save_dir_lyric:
            return
    else:
        save_dir_lyric = config["default_lyric_path"]

    progress_var.set(0)
    all_downloads_succeeded = True
    for item in items:
        song_id, song_name, _, _, source, _ = song_list.item(item, "values")
        success = download_music(song_id, song_name, source, save_dir_music, save_dir_lyric)
        if not success:
            all_downloads_succeeded = False
    progress_var.set(100)

    if all_downloads_succeeded:
        progress_var.set(100)
        messagebox.showinfo("完成", "所有选中歌曲下载完成")
    else:
        messagebox.showwarning("提示", "部分歌曲下载失败，请检查弹出的错误信息")

# ---------------- 设置窗口 ----------------
def open_settings():
    win = tk.Toplevel(root)
    win.title("设置")
    win.geometry("420x450")

    canvas = tk.Canvas(win)
    scrollbar = tk.Scrollbar(win, orient="vertical", command=canvas.yview)
    scroll_frame = tk.Frame(canvas)

    scroll_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    tk.Label(scroll_frame, text="默认音乐源:").pack(anchor="w", padx=10, pady=5)
    cb_source = ttk.Combobox(scroll_frame, values=ALL_SOURCES, state="readonly")
    cb_source.set(config.get("default_source", "netease"))
    cb_source.pack(anchor="w", padx=10)

    tk.Label(scroll_frame, text="默认搜索类型:").pack(anchor="w", padx=10, pady=5)
    cb_type = ttk.Combobox(scroll_frame, values=["单曲/歌手搜索", "专辑搜索"], state="readonly")
    cb_type.set(config.get("default_search_type", "单曲/歌手搜索"))
    cb_type.pack(anchor="w", padx=10)

    tk.Label(scroll_frame, text="默认音质:").pack(anchor="w", padx=10, pady=5)
    cb_bitrate = ttk.Combobox(scroll_frame, values=BITRATES, state="readonly")
    cb_bitrate.set(config.get("default_bitrate", "320"))
    cb_bitrate.pack(anchor="w", padx=10)

    tk.Label(scroll_frame, text="每页显示结果:").pack(anchor="w", padx=10, pady=5)
    cb_count = ttk.Combobox(scroll_frame, values=["10", "20", "30", "40", "50"], state="readonly")
    cb_count.set(config.get("default_search_count", 20))
    cb_count.pack(anchor="w", padx=10)

    tk.Label(scroll_frame, text="默认歌曲保存路径:").pack(anchor="w", padx=10, pady=5)
    entry_music_path = tk.Entry(scroll_frame, width=40)
    entry_music_path.insert(0, config.get("default_music_path", "每次询问"))
    entry_music_path.pack(anchor="w", padx=10)
    tk.Button(scroll_frame, text="选择路径", command=lambda: entry_music_path.delete(0, tk.END) or entry_music_path.insert(0, filedialog.askdirectory(parent=win))).pack(anchor="w", padx=10)

    tk.Label(scroll_frame, text="默认歌词保存路径:").pack(anchor="w", padx=10, pady=5)
    entry_lyric_path = tk.Entry(scroll_frame, width=40)
    entry_lyric_path.insert(0, config.get("default_lyric_path", "每次询问"))
    entry_lyric_path.pack(anchor="w", padx=10)
    tk.Button(scroll_frame, text="选择路径", command=lambda: entry_lyric_path.delete(0, tk.END) or entry_lyric_path.insert(0, filedialog.askdirectory(parent=win))).pack(anchor="w", padx=10)

    def save_and_close():
        config["default_source"] = cb_source.get()
        config["default_search_type"] = cb_type.get()
        config["default_bitrate"] = cb_bitrate.get()
        config["default_music_path"] = entry_music_path.get() or "每次询问"
        config["default_lyric_path"] = entry_lyric_path.get() or "每次询问"
        save_config(config)
        combo_source.set(config["default_source"])
        combo_search_type.set(config["default_search_type"])
        messagebox.showinfo("提示", "设置已保存并立即生效")
        win.destroy()

    tk.Button(scroll_frame, text="保存设置", command=save_and_close).pack(pady=20)

    canvas.pack(side="left", fill="both", expand=True)
    # scrollbar.pack(side="right", fill="y")

# ---------------- 点击跳转 & 封面 ----------------
def on_item_click(event):
    item_id = song_list.identify_row(event.y)
    col = song_list.identify_column(event.x)
    if not item_id:
        return

    values = song_list.item(item_id, "values")
    pic_id = values[5]
    if pic_id:
        show_album_cover(values[4], pic_id)

    if col == "#2":  # 歌名
        entry_keyword.delete(0, tk.END)
        entry_keyword.insert(0, values[1])
        combo_search_type.set("单曲/歌手搜索")
    elif col == "#3":  # 歌手
        entry_keyword.delete(0, tk.END)
        entry_keyword.insert(0, values[2])
        combo_search_type.set("单曲/歌手搜索")
    elif col == "#4":  # 专辑
        entry_keyword.delete(0, tk.END)
        entry_keyword.insert(0, values[3])
        combo_search_type.set("专辑搜索")

    handle_new_search()

def show_album_cover(source, pic_id):
    params = {
        "types": "pic",
        "source": source,
        "id": pic_id,
        "size": 300
    }
    album_label.config(image=None, text="封面加载中...")
    album_label.image = None

    thread = threading.Thread(target=_pic_worker, args=(params, pic_id), daemon=True)
    thread.start()

# ---------------- GUI ----------------
root = tk.Tk()
root.title("音乐搜索与下载")
root.geometry("1050x800")

# -------------  顶部出处标签  -------------
header_frame = tk.Frame(root)
header_frame.pack(side="top", fill="x", pady=(5,0))

link = tk.Label(header_frame,
                text="GD音乐台 (music.gdstudio.xyz)",
                fg="blue", cursor="hand2")
link.pack()

def open_url(event):
    webbrowser.open("https://music.gdstudio.xyz")
link.bind("<Button-1>", open_url)

# top frame contains search part and cover part
top_frame = tk.Frame(root)
top_frame.pack(side="top", fill="x", padx=10, pady=5)

left_frame = tk.Frame(top_frame)
left_frame.pack(side="left", fill="x", expand=True)

right_frame = tk.Frame(top_frame)
right_frame.pack(side="right", anchor="n", padx=(10, 0))

# main frame contains the rest
main_frame = tk.Frame(root)
main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

# left frame
tk.Label(left_frame, text="搜索关键词:").pack(anchor="w", padx=10, pady=5)
entry_keyword = tk.Entry(left_frame, width=50)
entry_keyword.pack(anchor="w", padx=10)

tk.Label(left_frame, text="音乐源:").pack(anchor="w", padx=10, pady=5)
combo_source = ttk.Combobox(left_frame, values=ALL_SOURCES, state="readonly")
combo_source.set(config.get("default_source", "netease"))
combo_source.pack(anchor="w", padx=10)

tk.Label(left_frame, text="搜索类型:").pack(anchor="w", padx=10, pady=5)
combo_search_type = ttk.Combobox(left_frame, values=["单曲/歌手搜索", "专辑搜索"], state="readonly")
combo_search_type.set(config.get("default_search_type", "单曲/歌手搜索"))
combo_search_type.pack(anchor="w", padx=10)

tk.Button(left_frame, text="搜索", command=handle_new_search).pack(anchor="w", padx=10, pady=5)

# right frame
tk.Label(right_frame, text="专辑封面").pack(pady=5)
album_label = tk.Label(right_frame)
album_label.pack(padx=5, pady=5)

# main frame
columns = ("id", "歌名", "歌手", "专辑", "音乐源", "pic_id")
song_list = ttk.Treeview(main_frame, columns=columns, show="headings", selectmode="extended")
for col in columns[:-1]:
    song_list.heading(col, text=col)
song_list.column("pic_id", width=0, stretch=tk.NO)
# song_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

# calculate w of treeview when resizing widget
def on_tree_resize(event):
    total_width = event.width - 20
    song_list.column("id", width=80, stretch=tk.NO, anchor='center')
    song_list.column("音乐源", width=100, stretch=tk.NO, anchor='center')
    remaining_width = total_width -80 -100

    if remaining_width > 0:
        song_list.column("歌名", width=int(remaining_width * 0.40), minwidth=120)
        song_list.column("歌手", width=int(remaining_width * 0.30), minwidth=100)
        song_list.column("专辑", width=int(remaining_width * 0.30), minwidth=120)

song_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
song_list.bind("<Configure>", on_tree_resize)

song_list.bind("<Double-1>", on_item_click)

frame_pages = tk.Frame(main_frame)
frame_pages.pack(pady=5)

def handle_prev_page():
    if current_keyword:
        search_music(current_keyword, current_source, current_search_type, max(1, current_page - 1))

tk.Button(frame_pages, text="上一页", command=handle_prev_page).pack(side=tk.LEFT, padx=5)

def handle_next_page():
    if current_keyword:
        search_music(current_keyword, current_source, current_search_type, current_page + 1)
tk.Button(frame_pages, text="下一页", command=handle_next_page).pack(side=tk.LEFT, padx=5)

tk.Button(main_frame, text="下载选中歌曲", command=download_selected).pack(pady=5)
tk.Button(main_frame, text="设置", command=open_settings).pack(pady=5)

tk.Label(main_frame, text="下载进度条：").pack(side="left")
progress_var = tk.IntVar()
progress_bar = ttk.Progressbar(main_frame, variable=progress_var, maximum=100)
progress_bar.pack(side="left", fill=tk.X, expand=True)

# -------------  新增：Ctrl+A 全选 & 鼠标拖动框选 -------------
# -------------  新增：Ctrl + A 全选 & 鼠标拖动框选 -------------
def tree_select_all(event):
    """Ctrl+A 全选"""
    song_list.selection_add(song_list.get_children())
    return "break"          # 防止系统默认再响一次

def _get_row_at_y(y):
    """根据 y 坐标返回对应的 iid，若空返回 None"""
    return song_list.identify_row(y)

def tree_start_select(event):
    """按下左键：记录起始行"""
    song_list._rb_start_y = event.y
    song_list._rb_start_item = _get_row_at_y(event.y)

def tree_update_select(event):
    """拖动：动态扩展选择"""
    if not hasattr(song_list, "_rb_start_y"):
        return
    cur_item = _get_row_at_y(event.y)
    if cur_item is None:
        return
    # 计算从起始行到当前行的区间
    all_items = song_list.get_children()
    try:
        from_idx = all_items.index(song_list._rb_start_item)
        to_idx = all_items.index(cur_item)
    except ValueError:
        return
    first, last = min(from_idx, to_idx), max(from_idx, to_idx)
    # 清除旧选，重选新区间
    song_list.selection_remove(*song_list.selection())
    song_list.selection_add(*all_items[first:last+1])

def tree_end_select(event):
    """松开左键：清理临时变量"""
    if hasattr(song_list, "_rb_start_y"):
        del song_list._rb_start_y, song_list._rb_start_item

# 绑定
root.bind_all("<Control-a>", tree_select_all, add='+')
song_list.bind("<Button-1>", tree_start_select, add='+')
song_list.bind("<B1-Motion>", tree_update_select, add='+')
song_list.bind("<ButtonRelease-1>", tree_end_select, add='+')

process_queue()
root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
