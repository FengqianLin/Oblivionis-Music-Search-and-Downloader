import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
from configure import *

class MainUI:
    def __init__(self, root):
        self.root = root
        self.setup_styles()
        self.create_widgets()

    def setup_styles(self):
        self.ui_font = tkFont.Font(family=UI_FONT_FAMILY, size=FIXED_UI_FONT_SIZE)
        style = ttk.Style()
        style.configure('.', font=self.ui_font)
        style.configure("Treeview.Heading", font=(UI_FONT_FAMILY, FIXED_UI_FONT_SIZE))
        style.configure("Treeview", font=self.ui_font)

    def create_widgets(self):
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(2, weight=1)

        # header frame
        header_frame = tk.Frame(self.root)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(5, 0))
        self.link = tk.Label(header_frame, text="GD音乐台 (music.gdstudio.xyz)", fg="blue", cursor="hand2",
                             font=self.ui_font)
        self.link.pack()

        # top frame
        top_frame = tk.Frame(self.root)
        top_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        top_frame.grid_columnconfigure(0, weight=3)
        top_frame.grid_columnconfigure(1, weight=1)
        top_frame.grid_rowconfigure(0, weight=1)

        # left frame search unit
        left_frame = tk.Frame(top_frame)
        left_frame.grid(row=0, column=0, sticky="nsew")
        right_frame = tk.Frame(top_frame)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        left_frame.grid_columnconfigure(1, weight=1)
        ttk.Label(left_frame, text="搜索关键词:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.entry_keyword = ttk.Entry(left_frame)
        self.entry_keyword.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=5)

        ttk.Label(left_frame, text="音乐源:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.combo_source = ttk.Combobox(left_frame, values=ALL_SOURCES, state="readonly")
        self.combo_source.grid(row=1, column=1, sticky="ew", padx=(0, 10), pady=5)

        ttk.Label(left_frame, text="搜索类型:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.combo_search_type = ttk.Combobox(left_frame, values=["单曲/歌手搜索", "专辑搜索", "网易云歌单搜索"], state="readonly")
        self.combo_search_type.grid(row=2, column=1, sticky="ew", padx=(0, 10), pady=5)

        self.btn_search = ttk.Button(left_frame, text="搜索")
        self.btn_search.grid(row=3, column=0, sticky="w", padx=10, pady=(5, 10))

        # button to import playlist. Wondering implementing it or not...
        # self.btn_import_playlist = ttk.Button(left_frame, text="导入歌单")
        # self.btn_import_playlist.grid(row=4, column=0, sticky="w", padx=10, pady=(5, 10))

        # right frame album unit
        right_frame.grid_rowconfigure(1, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)
        album_container = tk.Frame(right_frame, width=MAX_COVER_SIZE, height=MAX_COVER_SIZE)
        album_container.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        album_container.pack_propagate(False)
        self.album_label = tk.Label(album_container, text="无封面", font=self.ui_font)
        self.album_label.pack(expand=True, fill=tk.BOTH)

        # treeview song_list
        song_list_frame = tk.Frame(self.root)
        song_list_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))

        treeScrollbar = ttk.Scrollbar(song_list_frame, orient=tk.VERTICAL)
        columns = ("id", "歌名", "歌手", "专辑", "音乐源", "pic_id")
        self.song_list = ttk.Treeview(song_list_frame, columns=columns, show="headings", selectmode="extended",
                                      height=15, yscrollcommand=treeScrollbar.set)
        treeScrollbar.config(command=self.song_list.yview)
        for col in columns[:-1]:
            self.song_list.heading(col, text=col)
        self.song_list.column("pic_id", width=0, stretch=tk.NO)

        treeScrollbar.pack(side=tk.RIGHT, fill="y")
        self.song_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        frame_pages = tk.Frame(self.root)
        frame_pages.grid(row=3, column=0, sticky="ew", pady=5)
        frame_pages.grid_columnconfigure(0, weight=1);
        frame_pages.grid_columnconfigure(3, weight=1)
        self.btn_prev_page = ttk.Button(frame_pages, text="上一页")
        self.btn_prev_page.grid(row=0, column=1, padx=5)
        self.btn_next_page = ttk.Button(frame_pages, text="下一页")
        self.btn_next_page.grid(row=0, column=2, padx=5)

        # bottom button frame
        button_container_frame = tk.Frame(self.root)
        button_container_frame.grid(row=4, column=0, sticky="ew", pady=10)
        button_container_frame.grid_columnconfigure(0, weight=1)
        button_container_frame.grid_columnconfigure(2, weight=1)
        self.btn_download = ttk.Button(button_container_frame, text="下载选中歌曲")
        self.btn_download.grid(row=0, column=1, pady=(0, 5), sticky="ew")
        self.btn_settings = ttk.Button(button_container_frame, text="设置")
        self.btn_settings.grid(row=1, column=1, sticky="ew")

        # progressbar
        status_frame = tk.Frame(self.root)
        status_frame.grid(row=5, column=0, sticky="ew")
        status_frame.grid_columnconfigure(1, weight=1)
        tk.Label(status_frame, text="下载进度：", font=self.ui_font).grid(row=0, column=0, padx=10, pady=6, sticky="w")
        self.progress_var = tk.IntVar()
        progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, maximum=100)
        progress_bar.grid(row=0, column=1, padx=(0, 5), pady=6, sticky="ew")

        self.progress_task_var = tk.StringVar(value="0 / 0")
        self.progress_label = tk.Label(status_frame, textvariable=self.progress_task_var, font=self.ui_font, width=8,
                                       anchor='w')
        self.progress_label.grid(row=0, column=2, padx=(0, 10), pady=6, sticky="w")

        # tk.Label(status_frame, text="↓", font=self.ui_font).grid(row=0, column=3, pady=6, sticky='w')
        # self.speed_text_var = tk.StringVar(value="")
        # self.speed_label = tk.Label(status_frame, textvariable=self.speed_text_var, font=self.ui_font, width=12,
        #                             anchor='w')
        # self.speed_label.grid(row=0, column=4, padx=(0, 10), pady=6, sticky="w")