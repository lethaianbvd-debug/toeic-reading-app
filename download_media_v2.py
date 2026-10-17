"""
download_media_v2.py: Tự động quét TẤT CẢ các file đề thi (.json),
chỉ tải bù file media mới và chuyển đường dẫn sang offline.
"""

import os
import glob
import json
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

AUDIO_DIR = os.path.join("media", "audio")
IMAGES_DIR = os.path.join("media", "images")
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def download_file(url, save_path):
    if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
        return True, url, "Đã có sẵn"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=30) as response, open(save_path, "wb") as out_file:
            out_file.write(response.read())
        return True, url, "Thành công"
    except Exception as e:
        return False, url, str(e)

def process_all_tests():
    # Quét tất cả file json trong thư mục gốc và thư mục data/
    json_files = glob.glob("data/*.json") + [f for f in glob.glob("*.json") if f not in ("package.json", "config.json") and not f.endswith("_backup.json")]

    if not json_files:
        print("[!] Không tìm thấy file đề thi JSON nào.")
        return

    print(f"[*] Tìm thấy {len(json_files)} file đề thi: {', '.join(json_files)}")

    all_download_tasks = []
    file_data_map = {}

    for file_path in json_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = json.load(f)
            if not isinstance(content, list) or len(content) == 0 or "choices" not in content[0]:
                continue
            file_data_map[file_path] = content
            for q in content:
                media = q.get("media", {})
                for audio_url in media.get("audio", []):
                    if audio_url.startswith("http"):
                        fname = os.path.basename(urllib.parse.urlparse(audio_url).path)
                        all_download_tasks.append((audio_url, os.path.join(AUDIO_DIR, fname).replace("\\", "/")))
                for img_url in media.get("images", []):
                    if img_url.startswith("http"):
                        fname = os.path.basename(urllib.parse.urlparse(img_url).path)
                        all_download_tasks.append((img_url, os.path.join(IMAGES_DIR, fname).replace("\\", "/")))
        except Exception as e:
            print(f"[!] Bỏ qua {file_path}: {e}")

    unique_tasks = list({url: path for url, path in all_download_tasks}.items())
    pending_tasks = [(u, p) for u, p in unique_tasks if not (os.path.exists(p) and os.path.getsize(p) > 0)]

    print(f"[*] Tổng media: {len(unique_tasks)} | Đã có sẵn: {len(unique_tasks) - len(pending_tasks)} | Cần tải mới: {len(pending_tasks)}")

    if pending_tasks:
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(download_file, url, path): (url, path) for url, path in pending_tasks}
            for idx, future in enumerate(as_completed(futures), 1):
                success, url, msg = future.result()
                fname = os.path.basename(url)
                print(f"[{idx}/{len(pending_tasks)}] {'[OK]' if success else '[LỖI]'} {fname}")

    # Đồng bộ lại đường dẫn local cho các file JSON
    url_to_local_map = {url: path for url, path in unique_tasks}
    for file_path, questions in file_data_map.items():
        updated = False
        for q in questions:
            media = q.get("media", {})
            if "audio" in media:
                media["audio"] = [url_to_local_map.get(u, u) for u in media["audio"]]
                updated = True
            if "images" in media:
                media["images"] = [url_to_local_map.get(u, u) for u in media["images"]]
                updated = True
        if updated:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(questions, f, ensure_ascii=False, indent=2)
            print(f"  -> Cập nhật xong đường dẫn offline: {file_path}")

    print("\n[✔] XONG! Toàn bộ các bộ đề đã sẵn sàng chạy Offline.")

if __name__ == "__main__":
    process_all_tests()