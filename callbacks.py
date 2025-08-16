import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from io import BytesIO
import webbrowser
import threading

from download import *
from search import *

class AppCallbacks:
    def __init__(self, root, ui):
        self.root = root
        self.ui = ui
        self.config = load_config()
        self.settings_window = None
        self.download_errors = []
        self.failed_args = []

        self.current_keyword = ""
        self.current_source = ""
        self.current_search_type = ""
        self.current_page = 1

        self.ui.combo_source.set(self.config.get("default_source", "netease"))
        self.ui.combo_search_type.set(self.config.get("default_search_type", "单曲/歌手搜索"))
        self.download_semaphore = threading.Semaphore(self.config.get("max_concurrent_downloads", 3))

    def bind_callbacks(self):
        self.ui.link.bind("<Button-1>", self.open_url)
        self.ui.btn_search.config(command=self.handle_new_search)
        self.ui.root.bind("<Return>", lambda event: self.handle_new_search())
        self.ui.song_list.bind("<Configure>", self.on_tree_resize)
        self.ui.song_list.bind("<Double-1>", self.on_item_click)
        self.ui.btn_prev_page.config(command=self.handle_prev_page)
        self.ui.btn_next_page.config(command=self.handle_next_page)
        self.ui.btn_download.config(command=self.download_selected)
        self.ui.btn_settings.config(command=self.open_settings)

        self.root.bind_all("<Control-a>", self.tree_select_all, add='+')
        self.ui.song_list.bind("<Button-1>", self._tree_start_select, add='+')
        self.ui.song_list.bind("<B1-Motion>", self._tree_update_select, add='+')
        self.ui.song_list.bind("<ButtonRelease-1>", self._tree_end_select, add='+')

    # region update GUI
    def update_song_list(self, resp):
        self.ui.song_list.delete(*self.ui.song_list.get_children())
        if not resp:
            messagebox.showinfo("搜索提示", "未找到相关结果")
            return

        for song in resp:
            artist_str = ' / '.join(song["artist"]) if isinstance(song["artist"], list) else song["artist"]
            self.ui.song_list.insert("", tk.END, values=(
                song["id"], song["name"], artist_str, song["album"], song["source"], song.get("pic_id", "")
            ))
        self.ui.song_list.yview_moveto(0)

    def update_album_cover(self, img_data):
        try:
            img = Image.open(BytesIO(img_data))
            img.thumbnail((MAX_COVER_SIZE, MAX_COVER_SIZE), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.ui.album_label.config(image=photo, text="")
            self.ui.album_label.image = photo
        except Exception:
            self.ui.album_label.config(image=None, text="封面加载失败")
            self.ui.album_label.image = None

    # endregion

    # region threading
    def handle_new_search(self):
        keyword = self.ui.entry_keyword.get().strip()
        if not keyword:
            messagebox.showwarning("搜索提示", "请输入搜索内容")
            return
        source = self.ui.combo_source.get()
        search_type = self.ui.combo_search_type.get()
        self.search_music(keyword, source, search_type, page=1)

    def search_music(self, keyword, source, search_type, page=1):
        global search_id_counter
        self.ui.song_list.delete(*self.ui.song_list.get_children())
        self.ui.song_list.insert("", tk.END, values=("", "正在搜索，请稍候...", "", "", "", ""))
        self.root.update_idletasks()

        api_source = f"{source}_album" if search_type == "专辑搜索" else \
                        (f"{source}_playlist" if search_type == "网易云歌单搜索" else source)
        self.current_keyword = keyword
        self.current_source = source
        self.current_search_type = search_type
        self.current_page = page

        params = {
            "types": "search", "source": api_source, "name": keyword,
            "count": self.config.get("default_search_count", 20), "pages": page
        }
        # precise playlist search
        if search_type == "网易云歌单搜索" and self.current_keyword.isdigit() and len(self.current_keyword) >= 5:
            params = {
                "types": "playlist", "id": self.current_keyword
            }
        search_id_counter += 1
        thread = threading.Thread(target=search_worker, args=(params, search_id_counter), daemon=True)
        thread.start()

    def handle_prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.search_music(self.current_keyword, self.current_source, self.current_search_type, self.current_page)

    def handle_next_page(self):
        self.current_page += 1
        self.search_music(self.current_keyword, self.current_source, self.current_search_type, self.current_page)

    def process_queue(self):
        global search_id_counter, download_tasks_total, download_tasks_completed, all_downloads_succeeded
        # handle searching queue
        try:
            status, data, search_id = search_queue.get_nowait()
            if search_id == search_id_counter:
                if status == "success":
                    self.update_song_list(data)
                elif status == "error":
                    self.ui.song_list.delete(*self.ui.song_list.get_children())
                    messagebox.showerror("搜索歌曲错误", data)
        except queue.Empty:
            pass

        # handle pic queue
        try:
            status, data, pic_id = pic_queue.get_nowait()
            if status == "success":
                self.update_album_cover(data)
            elif status == "error":
                messagebox.showerror("搜索封面错误", data)
        except queue.Empty:
            pass

        # handle download queue
        try:
            status, data = download_queue.get_nowait()
            if status in ("success", "error"):
                download_tasks_completed += 1
                if download_tasks_total > 0:
                    progress = int(download_tasks_completed * 100 / download_tasks_total)
                    self.ui.progress_var.set(progress)

                if status == "error":
                    all_downloads_succeeded = False
                    error_message, retry_args = data
                    self.download_errors.append(error_message)
                    self.failed_args.append(retry_args)

                if download_tasks_completed >= download_tasks_total:
                    if all_downloads_succeeded:
                        messagebox.showinfo("下载完成", "所有选中歌曲下载成功！")
                    else:
                        success_count = download_tasks_total - len(self.download_errors)
                        error_summary = f"下载完成。成功 {success_count} 个, 失败 {len(self.download_errors)} 个。\n\n失败详情:\n"
                        detailed_errors = "\n".join(self.download_errors)

                        if messagebox.askyesno("下载完成", error_summary + detailed_errors \
                                                           + "\n\n是否重试失败的任务？" \
                                                           + "\n提示：\n如果下载时发生大量网络错误，请考虑减少同时下载任务数，然后重试。",
                                               parent=self.root):
                            self.retry_downloads()
                        else:
                            self.failed_args.clear()
        except queue.Empty:
            pass

        self.root.after(100, self.process_queue)

    # endregion

    # region download
    def download_selected(self):
        global download_tasks_total, download_tasks_completed, all_downloads_succeeded
        items = self.ui.song_list.selection()
        if not items:
            messagebox.showwarning("下载提示", "请选择要下载的歌曲")
            return

        # get music save path
        if self.config["default_music_path"] == "每次询问":
            save_dir_music = filedialog.askdirectory(title="选择音乐保存位置", parent=self.root)
            if not save_dir_music: return
        else:
            save_dir_music = self.config["default_music_path"]
            if not os.path.isdir(save_dir_music):
                try:
                    os.makedirs(save_dir_music, exist_ok=True)
                except Exception:
                    messagebox.showerror("路径错误", f"歌曲路径\n '{save_dir_music}' \n无法创建，请检查设置")
                    return

        # get lyric save path (only if mode需要保存 .lrc)
        save_dir_lyric = None
        lyric_mode = self.config.get("lyric_mode", "同时内嵌歌词并下载.lrc歌词文件")
        if lyric_mode in ["只下载.lrc歌词文件", "同时内嵌歌词并下载.lrc歌词文件"]:
            if self.config["default_lyric_path"] == "每次询问":
                save_dir_lyric = filedialog.askdirectory(title="选择歌词保存位置", parent=self.root)
                if not save_dir_lyric: return
            else:
                save_dir_lyric = self.config["default_lyric_path"]
                if not os.path.isdir(save_dir_lyric):
                    try:
                        os.makedirs(save_dir_lyric, exist_ok=True)
                    except Exception:
                        messagebox.showerror("路径错误", f"歌词路径\n '{save_dir_lyric}' \n无法创建，请检查设置")
                        return

        # start downloading
        self.ui.progress_var.set(0)
        download_tasks_total = len(items)
        download_tasks_completed = 0
        all_downloads_succeeded = True
        self.download_errors = []
        self.failed_args = []
        bitrate = self.config.get("default_bitrate", "320")
        cover_size = self.config.get("album_cover_size", 500)
        lyric_mode = self.config.get("lyric_mode", "同时内嵌歌词并下载.lrc歌词文件")
        record_type = self.config.get("record_number_type", "不编号")

        id_len = len(str(abs(len(items))))
        thread_id = 0
        for item in items:
            song_id, song_name, artist, album, source, pic_id = self.ui.song_list.item(item, "values")
            thread_str = None
            if record_type != "不编号":
                thread_id += 1
                thread_str = str(thread_id).zfill(id_len)
                if record_type == "只在元数据中编号":
                    thread_str += "."
                elif record_type == "只在文件名中编号":
                    thread_str += "!"
                elif record_type == "在元数据和文件名中编号":
                    thread_str += "+"
            thread = threading.Thread(
                target=download_worker,
                args=(thread_str, song_id, song_name, artist, album, source, pic_id, bitrate, cover_size, lyric_mode, save_dir_music, save_dir_lyric, self.download_semaphore),
                daemon=True
            )
            thread.start()

    def retry_downloads(self):
        global download_tasks_total, download_tasks_completed, all_downloads_succeeded

        if not self.failed_args:
            return

        # Reset counters and state for the retry
        self.ui.progress_var.set(0)
        download_tasks_total = len(self.failed_args)
        download_tasks_completed = 0
        all_downloads_succeeded = True

        # Keep a copy of args and clear the original lists for the next batch
        args_to_retry = self.failed_args[:]
        self.download_errors.clear()
        self.failed_args.clear()

        # Start new threads for the failed downloads
        for retry_args in args_to_retry:
            thread = threading.Thread(
                target=download_worker,
                args=retry_args,
                daemon=True
            )
            thread.start()
    # endregion

    def open_settings(self):
        if self.settings_window is not None and self.settings_window.winfo_exists():
            self.settings_window.lift()
            self.settings_window.focus_force()
            return

        win = tk.Toplevel(self.root)
        self.settings_window = win
        win.title("设置")
        win.geometry("400x600")  # 将窗口固定尺寸加大，以容纳所有设置
        win.resizable(False, True)
        win.minsize(400, 400)

        try:
            win.iconbitmap("assets/icon.ico")
        except tk.TclError:
            pass

        canvas = tk.Canvas(win)
        scrollbar = ttk.Scrollbar(win, orient="vertical", command=canvas.yview)
        main_frame = tk.Frame(canvas)
        main_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=main_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # region mousewheel
        def _on_mousewheel(event):
            if event.num == 4 or event.delta > 0:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5 or event.delta < 0:
                canvas.yview_scroll(1, "units")

        def _bind_mousewheel(event):
            win.bind_all("<MouseWheel>", _on_mousewheel)
            win.bind_all("<Button-4>", _on_mousewheel)
            win.bind_all("<Button-5>", _on_mousewheel)

        def _unbind_mousewheel(event):
            win.unbind_all("<MouseWheel>")
            win.unbind_all("<Button-4>")
            win.unbind_all("<Button-5>")

        main_frame.bind('<Enter>', _bind_mousewheel)
        main_frame.bind('<Leave>', _unbind_mousewheel)
        # endregion

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        ui_font = self.ui.ui_font

        # 默认音乐源
        tk.Label(main_frame, text="默认音乐源:", font=ui_font).pack(anchor="w", padx=10, pady=5)
        cb_source = ttk.Combobox(main_frame, values=ALL_SOURCES, state="readonly", font=ui_font)
        cb_source.set(self.config.get("default_source", "netease"))
        cb_source.pack(fill="x", padx=10)

        # 默认搜索类型
        tk.Label(main_frame, text="默认搜索类型:", font=ui_font).pack(anchor="w", padx=10, pady=5)
        cb_type = ttk.Combobox(main_frame, values=["单曲/歌手搜索", "专辑搜索"], state="readonly", font=ui_font)
        cb_type.set(self.config.get("default_search_type", "单曲/歌手搜索"))
        cb_type.pack(fill="x", padx=10)

        # 默认音质
        tk.Label(main_frame, text="默认音质:", font=ui_font).pack(anchor="w", padx=10, pady=5)
        cb_bitrate = ttk.Combobox(main_frame, values=BITRATES, state="readonly", font=ui_font)
        cb_bitrate.set(self.config.get("default_bitrate", "320"))
        cb_bitrate.pack(fill="x", padx=10)

        # 每页显示结果
        tk.Label(main_frame, text="每页显示结果:", font=ui_font).pack(anchor="w", padx=10, pady=5)
        cb_count = ttk.Combobox(main_frame, values=["10", "20", "30", "40", "50"], state="readonly", font=ui_font)
        cb_count.set(str(self.config.get("default_search_count", 20)))
        cb_count.pack(fill="x", padx=10)

        # 歌词处理方式
        tk.Label(main_frame, text="歌词处理方式:", font=ui_font).pack(anchor="w", padx=10, pady=5)
        cb_lyric_mode = ttk.Combobox(
            main_frame,
            values=["不下载歌词", "只内嵌歌词", "只下载.lrc歌词文件", "同时内嵌歌词并下载.lrc歌词文件"],
            state="readonly",
            font=ui_font
        )
        cb_lyric_mode.set(self.config.get("lyric_mode", "同时内嵌歌词并下载.lrc歌词文件"))
        cb_lyric_mode.pack(fill="x", padx=10)

        # 同时下载任务数
        tk.Label(main_frame, text="同时下载任务数:", font=ui_font).pack(anchor="w", padx=10, pady=5)
        cb_concurrency = ttk.Combobox(main_frame, values=["1", "2", "3", "4", "5", "6", "7", "8"], state="readonly", font=ui_font)
        cb_concurrency.set(str(self.config.get("max_downloads", 3)))
        cb_concurrency.pack(fill="x", padx=10)

        # 单次下载编号
        tk.Label(main_frame, text="为单次下载编号:", font=ui_font).pack(anchor="w", padx=10, pady=5)
        record_number_type = ttk.Combobox(main_frame, values=["不编号", "只在元数据中编号", "只在文件名中编号", "在元数据和文件名中编号"], state="readonly", font=ui_font)
        record_number_type.set(str(self.config.get("record_number_type", "不编号")))
        record_number_type.pack(fill="x", padx=10)

        # 默认歌曲保存路径
        tk.Label(main_frame, text="默认歌曲保存路径:", font=ui_font).pack(anchor="w", padx=10, pady=5)
        entry_music_path = tk.Entry(main_frame, width=40, font=ui_font)
        entry_music_path.insert(0, self.config.get("default_music_path", "每次询问"))
        entry_music_path.pack(fill="x", padx=10)
        tk.Button(main_frame, text="选择路径", font=ui_font, command=lambda: (entry_music_path.delete(0, tk.END),
                                                                                entry_music_path.insert(0,
                                                                                                        filedialog.askdirectory(
                                                                                                            parent=win) or "每次询问"))).pack(
            anchor="w", padx=10, pady=(2, 5))

        # 默认歌词保存路径
        tk.Label(main_frame, text="默认歌词保存路径:", font=ui_font).pack(anchor="w", padx=10, pady=5)
        entry_lyric_path = tk.Entry(main_frame, width=40, font=ui_font)
        entry_lyric_path.insert(0, self.config.get("default_lyric_path", "每次询问"))
        entry_lyric_path.pack(fill="x", padx=10)
        tk.Button(main_frame, text="选择路径", font=ui_font, command=lambda: (entry_lyric_path.delete(0, tk.END),
                                                                                entry_lyric_path.insert(0,
                                                                                                        filedialog.askdirectory(
                                                                                                            parent=win) or "每次询问"))).pack(
            anchor="w", padx=10, pady=(2, 5))

        # 专辑封面尺寸
        tk.Label(main_frame, text="专辑封面尺寸:", font=ui_font).pack(anchor="w", padx=10, pady=5)
        cb_cover_size = ttk.Combobox(main_frame, values=["300", "500"], state="readonly", font=ui_font)
        cb_cover_size.set(str(self.config.get("album_cover_size", 500)))
        cb_cover_size.pack(fill="x", padx=10)

        def on_settings_close():
            self.settings_window = None
            _unbind_mousewheel(None)
            win.destroy()

        def save_and_close():
            self.config["default_source"] = cb_source.get()
            self.config["default_search_type"] = cb_type.get()
            self.config["default_bitrate"] = cb_bitrate.get()
            self.config["default_search_count"] = int(cb_count.get())
            self.config["lyric_mode"] = cb_lyric_mode.get()
            self.config["max_downloads"] = int(cb_concurrency.get())
            self.config["record_number_type"] = record_number_type.get() or "不编号"
            self.config["default_music_path"] = entry_music_path.get().strip() or "每次询问"
            self.config["default_lyric_path"] = entry_lyric_path.get().strip() or "每次询问"
            self.config["album_cover_size"] = int(cb_cover_size.get())
            
            save_config(self.config)

            self.download_semaphore = threading.Semaphore(self.config["max_downloads"])
            self.ui.combo_source.set(self.config["default_source"])
            self.ui.combo_search_type.set(self.config["default_search_type"])

            messagebox.showinfo("提示", "设置已保存并立即生效", parent=win)
            on_settings_close()

        tk.Button(main_frame, text="保存设置", font=ui_font, command=save_and_close).pack(pady=20)
        win.protocol("WM_DELETE_WINDOW", on_settings_close)

    # region treeview item click
    def open_url(self, event):
        webbrowser.open("https://music.gdstudio.xyz")

    def on_item_click(self, event):
        item_id = self.ui.song_list.identify_row(event.y)
        col = self.ui.song_list.identify_column(event.x)
        if not item_id:
            return

        values = self.ui.song_list.item(item_id, "values")
        song_id, song_name, artist_name, album_name, source, pic_id = values
        if pic_id:
            self.show_album_cover(source, pic_id)

        target_keyword, search_type = None, None
        if col == "#2":
            target_keyword, search_type = song_name, "单曲/歌手搜索"
        elif col == "#3":
            target_keyword, search_type = artist_name, "单曲/歌手搜索"
        elif col == "#4":
            target_keyword, search_type = album_name, "专辑搜索"

        if target_keyword:
            self.ui.entry_keyword.delete(0, tk.END)
            self.ui.entry_keyword.insert(0, target_keyword)
            self.ui.combo_search_type.set(search_type)
            self.handle_new_search()

    def show_album_cover(self, source, pic_id):
        cover_size = self.config.get("album_cover_size", 500)
        params = {"types": "pic", "source": source, "id": pic_id, "size": cover_size}
        self.ui.album_label.config(image=None, text="封面加载中...")
        self.ui.album_label.image = None
        threading.Thread(target=pic_worker, args=(params, pic_id), daemon=True).start()

    def on_tree_resize(self, event):
        total_width = event.width - 20
        self.ui.song_list.column("id", width=80, stretch=tk.NO, anchor='center')
        self.ui.song_list.column("音乐源", width=100, stretch=tk.NO, anchor='center')
        remaining_width = total_width - 180
        if remaining_width > 0:
            self.ui.song_list.column("歌名", width=int(remaining_width * 0.40), minwidth=120)
            self.ui.song_list.column("歌手", width=int(remaining_width * 0.30), minwidth=100)
            self.ui.song_list.column("专辑", width=int(remaining_width * 0.30), minwidth=120)

    def tree_select_all(self, event):
        self.ui.song_list.selection_add(self.ui.song_list.get_children())
        return "break"

    def _get_row_at_y(self,  y):
        return self.ui.song_list.identify_row(y)

    def _tree_start_select(self, event):
        self.ui.song_list._rb_start_y = event.y
        self.ui.song_list._rb_start_item = self._get_row_at_y(event.y)

    def _tree_update_select(self, event):
        if not hasattr(self.ui.song_list, "_rb_start_y"): return
        cur_item = self._get_row_at_y(event.y)
        if cur_item is None: return

        all_items = self.ui.song_list.get_children()
        try:
            from_idx = all_items.index(self.ui.song_list._rb_start_item)
            to_idx = all_items.index(cur_item)
        except ValueError:
            return

        first, last = min(from_idx, to_idx), max(from_idx, to_idx)
        self.ui.song_list.selection_set(all_items[first:last + 1])

    def _tree_end_select(self, event):
        if hasattr(self.ui.song_list, "_rb_start_y"):
            del self.ui.song_list._rb_start_y
            del self.ui.song_list._rb_start_item
    # endregion
