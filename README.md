# Oblivionis Music Search and Downloader

**Oblivionis** is a Python-based desktop application designed for searching and downloading music from various online music platforms via the GD Studio Music API. It provides a user-friendly graphical interface to search for songs, albums, or artists, display album covers, and download music files and lyrics. The application supports multiple music sources and allows users to customize settings such as default music source, bitrate, and save paths.

## Disclaimer

This software is developed solely for integrating the API provided by GD Studio's Online Music Platform (music.gdstudio.xyz). The author of this software has no ownership or control over the music resources accessed through the API. All copyright-related responsibilities, including but not limited to the legality of music content, reside with GD Studio, the API provider. For any unlawful activity or copyright infringement concerns, please contact GD Studio at gdstudio@email.com.

The use of this software for any form of profit-making activity is strictly prohibited. Furthermore, the distribution of music resources obtained through this software is not permitted under any circumstances. Users are required to comply with the terms and conditions set forth by GD Studio, including the attribution of "GD音乐台 (music.gdstudio.xyz)" when utilizing the API.

By using this software, users acknowledge and agree to assume full legal responsibility for their actions in accordance with applicable laws, particularly those in mainland China. The author of this software shall not be held liable for any legal consequences arising from misuse or unauthorized activities.

## Features

- **Multi-Source Support**: Choose from a variety of music sources, with stable options like NetEase, Kuwo, and Joox (as of July 2025).
- **Album Cover Display**: Automatically fetch and display album artwork for selected tracks.
- **Configurable Settings**: Customize default music source, search type, bitrate(128kbps to lossless 999kbps), and save paths for music and lyrics.
- **User-Friendly Interface**: Built with Tkinter, featuring a responsive GUI with a progress bar, multi-selection, and mouse drag-to-select functionality.

## Prerequisites

To run the Python script, ensure you have the following dependencies installed:

- Python 3.11 or higher
- Required Python libraries:
  - Pillow
  - requests
  - mutagen

For the standalone `.exe` version, no additional dependencies are required.

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/FengqianLin/Oblivionis-Music-Search-and-Downloader.git
   cd Oblivionis-Music-Search-and-Downloader
   ```
2. **Set up a Virtual Environment**：
   ```bash
   conda create -n OblivionisMusic python=3.11
   conda activate OblivionisMusic
   ```
3. **Install Dependencies** (if running the Python script):
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Script**:
   ```bash
   python main.py
   ```
For the `.exe` version, download `Oblivionis.exe` from the [Releases](https://github.com/FengqianLin/Oblivionis-Music-Search-and-Downloader/releases) page and double-click to run.

## Usage

1. **Launch the Application**: Run the script or `.exe` file to open the GUI.
2. **Search for Music**:
   - Enter a keyword (song, artist, or album name) in the search bar.
   - Select a music source (e.g., NetEase, Kuwo) and search type (song/artist or album).
   - Click the "搜索" button to display results.
   - To search by an artist, album or playlist from your current results, double-click the artist/album/playlist cell for any song.
3. **View Album Covers**: Double-click the id or source cell in the results to fetch and display its album cover.
4. **Download Music**:
   - Select one or more songs from the results (use `Ctrl+A` to select all or drag to select multiple. You can also use `ctrl` or `shift` to select).
   - Click "下载选中歌曲" and choose save directories for music and lyrics (if not predefined in settings).
   - Monitor the download progress via the progress bar.
   - Now music metadata can also be downloaded.
5. **Customize Settings**:
   - Click the "设置" button to configure default music source, search type, bitrate, save paths, etc.
   - Save settings to apply them immediately and persist across sessions.
**Note**:
   - A high "同时下载任务数" could cause various issues. We recommend keeping it at **3 or below**.
   - The album search could fail in all situations. If you come across this issue, try removing '-' first, then 1 or 2spaces, and finally the artist name.

## API Information

Oblivionis uses the [GD Studio Music API](https://music.gdstudio.xyz) to fetch music data. Key API endpoints include:

- **Search**: `https://music-api.gdstudio.xyz/api.php?types=search&source=[MUSIC_SOURCE]&name=[KEYWORD]&count=[PAGE_LENGTH]&pages=[PAGE_NUM]`
- **Song URL**: `https://music-api.gdstudio.xyz/api.php?types=url&source=[MUSIC_SOURCE]&id=[TRACK_ID]&br=[BITRATE]`
- **Album Cover**: `https://music-api.gdstudio.xyz/api.php?types=pic&source=[MUSIC_SOURCE]&id=[PIC_ID]&size=[SIZE]`
- **Lyrics**: `https://music-api.gdstudio.xyz/api.php?types=lyric&source=[MUSIC_SOURCE]&id=[LYRIC_ID]`

## TODO

- [ ] Fix bug in album search
- [ ] Save playlist to disk (compatible with web version)
  - [ ] Import/Switch playlist
- [ ] Accelerate result display
- [ ] Cross-platform support
  - [ ] macOS
  - [ ] Android

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Make your changes and commit (`git commit -m "Add feature"`).
4. Push to the branch (`git push origin feature-branch`).
5. Create a pull request.

Please ensure your code adheres to the existing style and includes appropriate documentation.

## License

This project is licensed under the MIT License. See the [LICENSE](https://mit-license.org/) file for details.

## Acknowledgments

- **GD Studio**: For providing the music API and platform.
- **Community**: For feedback and contributions to improve the application.

## Contact

For issues, suggestions, or inquiries, please contact:

- **QJ Gao**: Gaoqijun0464@outlook.com

Our project is based on music.gdstudio.xyz. To contact the owner of website:
- **GD Studio**: gdstudio@email.com or via Bilibili (GD-Studio)
