# Auto Workshop Downloader

## Overview

**Auto Workshop Downloader** is a Python tool designed to automate downloading and extracting Steam Workshop items, primarily for Garry's Mod. It resolves dependencies of workshop addons, downloads them in batches using SteamCMD, and post-processes the downloads by extracting `.bin` and `.gma` files for easy use. (It can be used for other games also!)

---

## Features

- Resolves all required dependencies of workshop items automatically.
- Supports downloading individual items or entire collections (with GUI selection).
- Downloads using SteamCMD with optional Steam login or anonymous access.
- Post-processes downloads by extracting archives using 7-Zip and GMAD tools.
- Merges multiple extracted addons into a single folder.
- Handles missing tools (SteamCMD, GMAD, 7-Zip) with prompts and guidance.
- Customizable batch size, console color, and Steam AppID via config.
- Cross-platform with a simple console interface and Tkinter GUI for selections.

---

## Requirements

This project depends on the following Python packages (listed in `requirements.txt`):

- `requests`
- `beautifulsoup4`
- `ttkbootstrap`

Standard library modules used (no installation needed):

- `re`, `configparser`, `subprocess`, `os`, `shutil`, `time`, `tkinter`, `zipfile`

---

## Installation

1. Clone or download this repository.
2. Install Python 3.7+ if you haven't already.
3. Install dependencies with:

```bash
pip install -r requirements.txt
```

4. Configure the autoWorkshopDownloader.ini file (see below).
5. Ensure SteamCMD, GMAD, and 7-Zip executables are available or allow the script to download SteamCMD automatically.

## Configuration
```bash
[STEAM_AUTH]
username = 
password = 
[PATHS]
steamcmd_path = 
gmad_path = 
sevenzip_path = 
[OTHER]
app_id = 
batch_size = 
console_color = 
```

## Usage
Run the script:
```bash
python auto_workshop_downloader.py
```
- Enter Workshop item IDs or URLs (comma-separated).

- If collections are entered, a GUI will prompt you to select specific items to download.

- The script resolves dependencies, downloads items in batches, extracts addons, and optionally merges them.

- If SteamCMD is missing, you’ll be prompted to download it automatically.

- If Steam credentials are missing or invalid, anonymous login will be attempted with a warning.

- Batch sizes above 30 are discouraged as SteamCMD may timeout and cause infinite download loops.

- 7-Zip and GMAD must be installed manually or set in config; the script provides guidance if missing.

## Notes
- Currently, app_id support is tailored for Garry's Mod Workshop items. Other games may require code adjustments.

- GMAD cannot be downloaded automatically due to Steam restrictions; it must be manually installed with Garry's Mod.

- 7-Zip can be downloaded from https://www.7-zip.org/download.html.

- Console colors are Windows-specific; on other platforms, color codes may be ignored.

## License
This project is open source and available under the MIT License.

## Contributions
Contributions and forks are welcome! Feel free to add support for other Steam games, improve UI, or enhance automation.

## Known Issues
- When copying downloads from steamcmd/steamapps/workshop/content, all folders are copied, not just the ones that were downloaded.

- The script errors out when pasting links during a second run.

- If Steam authentication fails, the script still proceeds to the extraction step instead of stopping.