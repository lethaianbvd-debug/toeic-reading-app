"""
Script tự động tải toàn bộ Audio (MP3) và Hình ảnh từ data.json về máy
và cập nhật lại đường dẫn local để app TOEIC chạy hoàn toàn Offline 100%.
"""

import os
import json
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

JSON_FILE = "data.json"
BACKUP_FILE = "data_backup.json"
AUDIO_DIR = os.path.join("media", "audio")
IMAGES_DIR = os.path.join("media", "images")

# 1. Tự động tạo thư mục media/audio và media/images nếu chưa có
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

# Giả lập header trình duyệt tránh bị máy chủ chặn tải tự động
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def download_file(url, save_path):
    """Tải một file và tự động bỏ qua nếu file đã tải xong trước đó."""
    if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
        return True, url, "Đã có sẵn (bỏ qua)"
    
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=30) as response, open(save_path, "wb") as out_file:
            out_file.write(response.read())
        return True, url, "Thành công"
    except Exception as e:
        return False, url, str(e)

def main():
    if not os.path.exists(JSON_FILE):
        print(f"[!] Không tìm thấy tệp {JSON_FILE} trong thư mục hiện tại.")
        return

    print(f"[*] Đang đọc {JSON_FILE}...")
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        questions = json.load(f)

    # Tự động tạo một bản sao lưu gốc data_backup.json phòng trường hợp cần khôi phục
    if not os.path.exists(BACKUP_FILE):
        with open(BACKUP_FILE, "w", encoding="utf-8") as f:
            json.dump(questions, f, ensure_ascii=False, indent=2)
        print(f"[+] Đã tạo bản sao lưu dự phòng: {BACKUP_FILE}")

    # Thu thập toàn bộ URL cần tải
    download_tasks = []
    url_to_local_map = {}

    for q in questions:
        media = q.get("media", {})
        
        # Lấy danh sách Audio
        for audio_url in media.get("audio", []):
            if audio_url.startswith("http"):
                filename = os.path.basename(urllib.parse.urlparse(audio_url).path)
                local_path = os.path.join(AUDIO_DIR, filename).replace("\\", "/")
                url_to_local_map[audio_url] = local_path
                download_tasks.append((audio_url, local_path))

        # Lấy danh sách Hình ảnh
        for img_url in media.get("images", []):
            if img_url.startswith("http"):
                filename = os.path.basename(urllib.parse.urlparse(img_url).path)
                local_path = os.path.join(IMAGES_DIR, filename).replace("\\", "/")
                url_to_local_map[img_url] = local_path
                download_tasks.append((img_url, local_path))

    # Loại bỏ các link bị trùng lặp
    unique_tasks = list({url: path for url, path in download_tasks}.items())
    print(f"[*] Tìm thấy tổng cộng {len(unique_tasks)} tệp media cần tải...")

    # Chạy tải 8 luồng song song (tốc độ cao)
    success_count = 0
    fail_count = 0

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(download_file, url, path): (url, path) for url, path in unique_tasks}
        for idx, future in enumerate(as_completed(futures), 1):
            success, url, msg = future.result()
            filename = os.path.basename(url)
            if success:
                success_count += 1
                print(f"[{idx}/{len(unique_tasks)}] [OK] {filename}")
            else:
                fail_count += 1
                print(f"[{idx}/{len(unique_tasks)}] [LỖI] {filename} -> {msg}")

    print(f"\n[*] Hoàn tất tải file: {success_count} thành công, {fail_count} thất bại.")

    # Cập nhật lại các link online trong data.json thành đường dẫn thư mục cục bộ
    print(f"[*] Đang cập nhật lại đường dẫn trong {JSON_FILE}...")
    for q in questions:
        media = q.get("media", {})
        if "audio" in media:
            media["audio"] = [url_to_local_map.get(u, u) for u in media["audio"]]
        if "images" in media:
            media["images"] = [url_to_local_map.get(u, u) for u in media["images"]]

    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)

    print(f"[✔] THÀNH CÔNG! File {JSON_FILE} đã được chuyển sang chế độ Offline.")
    print("    Bạn có thể ngắt mạng Internet và kiểm tra lại trên trình duyệt!")

if __name__ == "__main__":
    main()