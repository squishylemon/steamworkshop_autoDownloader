import requests
from bs4 import BeautifulSoup
import re
import configparser
import subprocess
import os
import shutil
import time
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import zipfile

INI_FILE = "autoWorkshopDownloader.ini"
APPID = "0"  # load_from_config now

ASCII_ART = r"""
 _____                                                                                     _____ 
( ___ )                                                                                   ( ___ )
 |   |~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~|   | 
 |   |                                                                                     |   | 
 |   |                 _        _____                      _                 _             |   | 
 |   |      /\        | |      |  __ \                    | |               | |            |   | 
 |   |     /  \  _   _| |_ ___ | |  | | _____      ___ __ | | ___   __ _  __| | ___ _ __   |   | 
 |   |    / /\ \| | | | __/ _ \| |  | |/ _ \ \ /\ / / '_ \| |/ _ \ / _` |/ _` |/ _ \ '__|  |   | 
 |   |   / ____ \ |_| | || (_) | |__| | (_) \ V  V /| | | | | (_) | (_| | (_| |  __/ |     |   | 
 |   |  /_/    \_\__,_|\__\___/|_____/ \___/ \_/\_/ |_| |_|_|\___/ \__,_|\__,_|\___|_|     |   | 
 |   |                                                                                     |   | 
 |___|~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~|___| 
(_____)                                                                                   (_____)
"""

def download_and_extract_steamcmd(dest_dir):
    url = "https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip"
    local_zip = os.path.join(dest_dir, "steamcmd.zip")

    os.makedirs(dest_dir, exist_ok=True)

    print("[*] Downloading SteamCMD...")
    with requests.get(url, stream=True) as r:
        with open(local_zip, "wb") as f:
            shutil.copyfileobj(r.raw, f)

    print("[*] Extracting SteamCMD...")
    with zipfile.ZipFile(local_zip, 'r') as zip_ref:
        zip_ref.extractall(dest_dir)

    os.remove(local_zip)
    print(f"[✓] SteamCMD extracted to: {dest_dir}")
    return os.path.join(dest_dir, "steamcmd.exe")

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_required_ids_and_title(item_id):
    url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={item_id}"
    resp = requests.get(url)
    if resp.status_code != 200:
        print(f"[!] Failed to fetch {url}")
        return [], "Unknown Title"

    soup = BeautifulSoup(resp.text, "html.parser")

    title_elem = soup.select_one('.workshopItemTitle')
    title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"

    required = []
    for a_tag in soup.select('#RequiredItems a'):
        href = a_tag.get('href')
        if href:
            match = re.search(r'id=(\d+)', href)
            if match:
                dep_id = match.group(1)
                required.append(dep_id)

    return required, title

def get_collection_items(collection_id):
    url = f"https://steamcommunity.com/workshop/filedetails/?id={collection_id}"
    resp = requests.get(url)
    if resp.status_code != 200:
        print(f"[!] Failed to fetch collection page: {url}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    items = []
    # This selector picks only the title inside collectionItem
    for item_div in soup.select('.collectionItem'):
        link = item_div.select_one('a[href*="filedetails"]')
        title_elem = item_div.select_one('.workshopItemTitle')
        if link and title_elem:
            href = link.get('href')
            match = re.search(r'id=(\d+)', href)
            if match:
                title = title_elem.get_text(strip=True)
                items.append((match.group(1), title))

    return items

def select_from_collection_gui(items):
    root = ttk.Window(themename="darkly")
    root.title("Select Workshop Items")
    root.geometry("760x520")
    root.minsize(760, 520)

    header = ttk.Label(root, text="Select items to download", font=("Segoe UI", 18, "bold"))
    header.pack(pady=(20, 15))

    container = ttk.Frame(root, padding=10)
    container.pack(fill="both", expand=True, padx=15, pady=(0,15))

    canvas = tk.Canvas(container, background="#1e1e1e", highlightthickness=0)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview, bootstyle="dark")

    scrollable_frame = ttk.Frame(canvas, bootstyle="secondary")

    def on_frame_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))

    scrollable_frame.bind("<Configure>", on_frame_configure)

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Mouse wheel scroll
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    canvas.bind_all("<MouseWheel>", _on_mousewheel)
    canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))  # Linux scroll up
    canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))   # Linux scroll down


    selected = {}
    for item_id, title in items:
        var = ttk.BooleanVar()
        label_text = f"{title} [{item_id}]"
        chk = ttk.Checkbutton(scrollable_frame, text=label_text, variable=var, bootstyle="success-round-toggle")
        chk.pack(anchor="w", padx=15, pady=6, fill="x")
        selected[item_id] = var

    submit_btn = ttk.Button(root, text="Download Selected", bootstyle="success-outline", command=lambda: submit())
    submit_btn.pack(pady=(10, 20))

    def submit():
        root.selected_items = [item_id for item_id, var in selected.items() if var.get()]
        root.destroy()

    root.mainloop()
    return getattr(root, "selected_items", [])
def resolve_all(start_ids):
    seen = {}
    to_process = list(start_ids)

    while to_process:
        item_id = to_process.pop()
        if item_id not in seen:
            deps, title = get_required_ids_and_title(item_id)
            seen[item_id] = title
            print(f"[+] {item_id}: {title}")
            to_process.extend(deps)

    return seen

def load_config():
    config = configparser.ConfigParser()
    config.read(INI_FILE)

    username = config.get("STEAM_AUTH", "username")
    password = config.get("STEAM_AUTH", "password")
    steamcmd_path = config.get("PATHS", "steamcmd_path")
    gmad_path = config.get("PATHS", "gmad_path")
    sevenzip_path = config.get("PATHS", "sevenzip_path")
    download_batch_size = config.getint("OTHER", "batch_size")
    app_id = config.getint("OTHER", "app_id")
    console_color = config.get("OTHER", "console_color", fallback="07")

    workshop_dir = os.path.join(os.path.dirname(steamcmd_path), "steamapps", "workshop", "content")

    return username, password, steamcmd_path, gmad_path, sevenzip_path, download_batch_size, workshop_dir, console_color, app_id

def run_steamcmd(steamcmd_path, username, password, items, batch_size):
    item_ids = list(items.keys())
    total = len(item_ids)
    batches = [item_ids[i:i+batch_size] for i in range(0, total, batch_size)]

    print(f"[✓] Running SteamCMD in {len(batches)} batch(es) of up to {batch_size} items each...")

    for idx, batch in enumerate(batches, 1):
        print(f"[*] Starting batch {idx}/{len(batches)} ({len(batch)} items)...")
        cmd = [steamcmd_path, "+login", username, password]
        for item_id in batch:
            cmd.extend(["+workshop_download_item", str(APPID), str(item_id)])
        cmd.append("+quit")

        print(" ".join([c if c != password else "******" for c in cmd]))

        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"[!] SteamCMD failed on batch {idx}: {e}")
            break

def sanitize_folder_name(name):
    return re.sub(r'[\\/*?:"<>|]', '_', name)

def merge_extracted_addons(auto_extracts):
    merged_dir = os.path.join(auto_extracts, "merged_addons")
    os.makedirs(merged_dir, exist_ok=True)

    addon_folders = [f for f in os.listdir(auto_extracts)
                     if os.path.isdir(os.path.join(auto_extracts, f)) and f != "merged_addons"]

    print(f"[*] Merging {len(addon_folders)} addon(s) into '{merged_dir}' ...")

    for folder in addon_folders:
        folder_path = os.path.join(auto_extracts, folder)

        for root, dirs, files in os.walk(folder_path):
            rel_path = os.path.relpath(root, folder_path)
            target_dir = os.path.join(merged_dir, rel_path)
            os.makedirs(target_dir, exist_ok=True)

            for file in files:
                src_file = os.path.join(root, file)
                dst_file = os.path.join(target_dir, file)

                if os.path.exists(dst_file):
                    base, ext = os.path.splitext(file)
                    dst_file = os.path.join(target_dir, f"{base}_{folder}{ext}")

                shutil.move(src_file, dst_file)

        try:
            shutil.rmtree(folder_path)
        except Exception as e:
            print(f"[!] Failed to remove {folder_path}: {e}")

    print("[✓] Merge complete.")

def cleanup_workshop_content(workshop_dir):
    if not os.path.isdir(workshop_dir):
        print(f"[!] Workshop content folder not found: {workshop_dir}")
        return

    for entry in os.listdir(workshop_dir):
        entry_path = os.path.join(workshop_dir, entry)
        if os.path.isdir(entry_path):
            try:
                shutil.rmtree(entry_path)
                print(f"[✓] Removed workshop content folder: {entry_path}")
            except Exception as e:
                print(f"[!] Failed to remove {entry_path}: {e}")


def post_process_downloads(gmad_path, sevenzip_path, resolved, workshop_dir_base):
    workshop_dir = os.path.join(workshop_dir_base, str(APPID))
    auto_downloads = os.path.join(os.getcwd(), "autoDownloads")
    auto_extracts = os.path.join(os.getcwd(), "autoExtracts")

    os.makedirs(auto_downloads, exist_ok=True)
    os.makedirs(auto_extracts, exist_ok=True)

    downloaded = 0
    extracted = 0

    for item_id in os.listdir(workshop_dir):
        item_path = os.path.join(workshop_dir, item_id)
        if not os.path.isdir(item_path):
            continue

        downloaded += 1
        addon_title = resolved.get(item_id, "Unknown Addon")
        safe_folder_name = f"{sanitize_folder_name(addon_title)} [{item_id}]"
        extract_folder_path = os.path.join(auto_extracts, safe_folder_name)

        print(f"[*] Processing item {item_id} - '{addon_title}'...")

        for file in os.listdir(item_path):
            file_path = os.path.join(item_path, file)

            if file.endswith(".bin"):
                print(f"[*] Extracting BIN with 7zip: {file}")

                extract_dest = os.path.join(item_path, "extracted")
                os.makedirs(extract_dest, exist_ok=True)

                try:
                    subprocess.run([sevenzip_path, "x", file_path, f"-o{extract_dest}", "-y"], check=True)
                except subprocess.CalledProcessError as e:
                    print(f"[!] 7zip extraction error (usually harmless): {e}")

                extracted_files = [f for f in os.listdir(extract_dest) if os.path.isfile(os.path.join(extract_dest, f))]
                if not extracted_files:
                    print(f"[!] No files extracted from {file_path}")
                    continue

                extracted_file = extracted_files[0]
                extracted_path = os.path.join(extract_dest, extracted_file)

                gma_path = extracted_path + ".gma"
                os.rename(extracted_path, gma_path)
                print(f"[*] Renamed extracted file to {gma_path}")

                os.makedirs(extract_folder_path, exist_ok=True)
                try:
                    subprocess.run([gmad_path, "extract", "-file", gma_path, "-out", extract_folder_path], check=True)
                    print(f"[✓] Extracted .gma with GMAD: {gma_path} -> {extract_folder_path}")
                    extracted += 1
                except subprocess.CalledProcessError as e:
                    print(f"[!] GMAD extraction failed: {e}")

                shutil.move(file_path, os.path.join(auto_downloads, f"{item_id}_{file}"))
                shutil.rmtree(extract_dest)

            elif file.endswith(".gma"):
                print(f"[*] Found GMA: {file}")
                os.makedirs(extract_folder_path, exist_ok=True)
                subprocess.run([gmad_path, "extract", "-file", file_path, "-out", extract_folder_path], check=True)
                print(f"[✓] Extracted: {file_path} -> {extract_folder_path}")
                shutil.move(file_path, os.path.join(auto_downloads, f"{item_id}_{file}"))
                extracted += 1

        shutil.rmtree(item_path)

    return downloaded, extracted

def parse_input_ids(user_input):
    parts = [x.strip() for x in user_input.split(",") if x.strip()]
    ids = []

    for p in parts:
        match = re.search(r'id=(\d+)', p)
        if match:
            id_ = match.group(1)
            # Try fetching as collection
            collection_items = get_collection_items(id_)
            if collection_items:
                print(f"[*] Detected collection with {len(collection_items)} items.")
                selected = select_from_collection_gui(collection_items)
                ids.extend(selected)
            else:
                ids.append(id_)
        elif p.isdigit():
            ids.append(p)
        else:
            print(f"[!] Ignoring invalid input: {p}")

    return ids

if __name__ == "__main__":
    username, password, steamcmd_path, gmad_path, sevenzip_path, download_batch_size, workshop_dir, console_color, app_id = load_config()

    APPID = app_id
    cur_dir = os.getcwd()

    # -- SteamCMD --
    if not os.path.isfile(steamcmd_path):
        print("[!] SteamCMD not found.")
        choice = input(f"Would you like to download it to {cur_dir}/steamcmd/? (y/n): ").strip().lower()
        if choice != "y":
            print("Exiting. SteamCMD is required.")
            exit(1)
        steamcmd_path = download_and_extract_steamcmd(os.path.join(cur_dir, "steamcmd"))
        workshop_dir = os.path.join(os.path.dirname(steamcmd_path), "steamapps", "workshop", "content")
        print(f"[✓] Updated steamcmd_path: {steamcmd_path}")

    # -- GMAD --
    if not os.path.isfile(gmad_path):
        print("[!] GMAD not found.")
        print("Please copy gmad.exe manually from your Garry's Mod 'bin' folder.")
        print("Example path: steamapps/common/garrysmod/bin/gmad.exe")
        input("Press Enter to continue or Ctrl+C to exit...")

    # -- 7zip --
    if not os.path.isfile(sevenzip_path):
        print("[!] 7zip not found.")
        print("Please install it manually from: https://www.7-zip.org/download.html")
        input("Press Enter to continue or Ctrl+C to exit...")


    # -- Account credentials --
    if not username or not password or len(username) < 3 or len(password) < 3:
        username = "anonymous"
        password = ""
        print("[!] No valid account details found. Using anonymous login. This may fail for some APPIDs.")
        input("Press Enter to continue...")


    # -- Batch size sanity check --
    if download_batch_size > 30:
        print("[!] WARNING: Batch size is larger than 30.")
        print("This may cause Steam login to timeout or hang forever. Recommend keeping batch size <= 30.")
        input("Press Enter to continue...")

    # -- APPID notice --
    if APPID != 4000:
        print(f"[i] APPID is set to {APPID}.")
        print("[i] This script is mainly built for Garry's Mod (4000). Feel free to fork for other games.")

    while True:
        clear_console()
        os.system(f'color {console_color}')
        print(ASCII_ART)
        user_input = input("Enter Workshop IDs or URLs (comma separated): ").strip()
        if not user_input:
            print("No input given. Exiting.")
            break

        start_ids = parse_input_ids(user_input)
        if not start_ids:
            print("No valid IDs found. Please try again.")
            continue

        start_time = time.time()
        print("[*] Resolving dependency tree...")
        resolved = resolve_all(start_ids)

        print(f"[✓] Total unique items (including dependencies): {len(resolved)}")
        for item_id, title in resolved.items():
            print(f"{item_id} - {title}")

        run_steamcmd(steamcmd_path, username, password, resolved, download_batch_size)

        print("[*] Post-processing downloaded files...")
        downloaded, extracted = post_process_downloads(gmad_path, sevenzip_path, resolved, workshop_dir)

        elapsed = time.time() - start_time
        os.system(f'color {console_color}')
        print(f"\n[✓] Summary: Downloaded {downloaded} addons, extracted {extracted} addons in {elapsed:.1f} seconds.\n")

        if APPID == 4000:
            ans = input("Do you want to merge all extracted addons into one folder? (y/n): ").strip().lower()
            if ans == "y":
                auto_extracts = os.path.join(os.getcwd(), "autoExtracts")
                merge_extracted_addons(auto_extracts)

        cleanup_workshop_content(workshop_dir)

        cont = input("Do you want to download more addons? (y/n): ").strip().lower()
        if cont != "y":
            print("Exiting.")
            break
