# Oblivionis Music Search and Downloader

**Oblivionis** is a Python-based desktop application designed for searching and downloading music from various online music platforms via the GD Studio Music API. It provides a user-friendly graphical interface to search for songs, albums, or artists, display album covers, and download music files and lyrics. The application supports multiple music sources and allows users to customize settings such as default music source, bitrate, and save paths.

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
   python Oblivionis.py
   ```
For the `.exe` version, download `Oblivionis.exe` from the [Releases](https://github.com/FengqianLin/Oblivionis-Music-Search-and-Downloader/releases) page and double-click to run.

## Usage

1. **Launch the Application**: Run the script or `.exe` file to open the GUI.
2. **Search for Music**:
   - Enter a keyword (song, artist, or album name) in the search bar.
   - Select a music source (e.g., NetEase, Kuwo) and search type (song/artist or album).
   - Click the "搜索" button to display results.
   - To search by an artist or album from your current results, double-click the artist or album cell for any song.
3. **View Album Covers**: Double-click a song in the results to fetch and display its album cover.
4. **Download Music**:
   - Select one or more songs from the results (use `Ctrl+A` to select all or drag to select multiple. You can also use `ctrl` or `shift` to select).
   - Click "下载选中歌曲" and choose save directories for music and lyrics (if not predefined in settings).
   - Monitor the download progress via the progress bar.
5. **Customize Settings**:
   - Click the "设置" button to configure default music source, search type, bitrate, and save paths.
   - Save settings to apply them immediately and persist across sessions.
6. **Cookie Management**:
   - This app automatically creates a cookie file `session_cookies.pkl`. You can safely delete this file at any time.

## API Information

Oblivionis uses the [GD Studio Music API](https://music.gdstudio.xyz) to fetch music data. Key API endpoints include:

- **Search**: `https://music-api.gdstudio.xyz/api.php?types=search&source=[MUSIC_SOURCE]&name=[KEYWORD]&count=[PAGE_LENGTH]&pages=[PAGE_NUM]`
- **Song URL**: `https://music-api.gdstudio.xyz/api.php?types=url&source=[MUSIC_SOURCE]&id=[TRACK_ID]&br=[BITRATE]`
- **Album Cover**: `https://music-api.gdstudio.xyz/api.php?types=pic&source=[MUSIC_SOURCE]&id=[PIC_ID]&size=[SIZE]`
- **Lyrics**: `https://music-api.gdstudio.xyz/api.php?types=lyric&source=[MUSIC_SOURCE]&id=[LYRIC_ID]`

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
