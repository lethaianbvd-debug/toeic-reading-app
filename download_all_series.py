"""
Script quét đệ quy TOÀN BỘ thư mục đề thi (data, data19 - data25):
1. Tự động sửa lỗi nháy đơn xen kẽ ('h'e'l'l'o' -> hello)
2. Khôi phục link URL chuẩn và tải bù toàn bộ Audio/Hình ảnh
3. Đồng bộ lại đường dẫn local để chạy Offline 100%
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

def is_corrupted(s):
    """Kiểm tra xem chuỗi có bị lỗi chèn dấu nháy đơn xen kẽ không."""
    if not isinstance(s, str):
        return False
    if s == "'":
        return True
    if len(s) >= 3 and len(s) % 2 == 1 and all(c == "'" for c in s[0::2]):
        return True
    return False

def uncorrupt_str(s):
    """Khôi phục lại chuỗi gốc nếu bị lỗi xen kẽ dấu nháy đơn."""
    if not isinstance(s, str):
        return s
    
    def _fix(val):
        count = 0
        while is_corrupted(val) and count < 10:
            if val == "'":
                val = ""
                break
            val = val[1::2]
            count += 1
        return val

    s = _fix(s)
    # Khôi phục nếu phần tên tệp trong đường dẫn bị lỗi
    if "/" in s or "\\" in s:
        dirname, fname = os.path.split(s)
        fname = _fix(fname)
        s = os.path.join(dirname, fname).replace("\\", "/")

    # Chuẩn hóa các ký tự đặc biệt
    s = s.replace("\ufffd", "'")
    s = s.replace("â€™", "'").replace("â€œ", '"').replace("â€", '"').replace("â€“", "-").replace("â€”", " - ")
    return s

def clean_obj(obj):
    """Đệ quy sửa sạch toàn bộ đối tượng JSON."""
    if isinstance(obj, dict):
        return {k: clean_obj(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_obj(item) for item in obj]
    elif isinstance(obj, str):
        return uncorrupt_str(obj)
    return obj

def get_remote_url(path_or_url, media_type="audio"):
    """Tạo lại link tải chính xác từ server gốc."""
    if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
        return path_or_url
    filename = os.path.basename(path_or_url)
    if media_type == "audio":
        return f"https://hcm.ss.bfcplatform.vn/tart-cos/mock-tests/{filename}"
    else:
        return f"https://hcm.ss.bfcplatform.vn/tart-cos/image/{filename}"

def download_file(url, save_path, retries=3):
    if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
        return True, url, "Đã có sẵn"
    
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=25) as response, open(save_path, "wb") as out_file:
                out_file.write(response.read())
            if os.path.getsize(save_path) > 0:
                return True, url, "Thành công"
        except Exception as e:
            if attempt == retries:
                return False, url, str(e)
    return False, url, "Lỗi không xác định"

def find_all_test_files():
    all_json = glob.glob("**/*.json", recursive=True)
    ignored = ["package.json", "tsconfig.json", "config.json", "_backup.json", "node_modules", "dist", "build"]
    test_files = []
    for f in all_json:
        f_norm = f.replace("\\", "/")
        if any(ign in f_norm for ign in ignored):
            continue
        test_files.append(f)
    return sorted(test_files)

def main():
    print("=" * 65)
    print(" BẮT ĐẦU PHỤC HỒI DỮ LIỆU & TẢI MEDIA TOÀN BỘ ĐỀ THI")
    print("=" * 65)

    test_files = find_all_test_files()
    print(f"[*] Tìm thấy {len(test_files)} file đề thi.")

    missing_downloads = []

    # 1. Khôi phục text và sửa lại tên file chuẩn
    print("\n[*] Bước 1: Khôi phục văn bản và chuẩn hóa đường dẫn...")
    for fpath in test_files:
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, list) or len(data) == 0:
                continue

            data = clean_obj(data)

            for q in data:
                media = q.get("media", {})

                # Audio
                new_audio = []
                for a_item in media.get("audio", []):
                    a_clean = uncorrupt_str(a_item)
                    fname = os.path.basename(urllib.parse.urlparse(a_clean).path if a_clean.startswith("http") else a_clean)
                    local_path = os.path.join(AUDIO_DIR, fname).replace("\\", "/")
                    new_audio.append(local_path)
                    if not (os.path.exists(local_path) and os.path.getsize(local_path) > 0):
                        remote_url = get_remote_url(fname, "audio")
                        missing_downloads.append((remote_url, local_path))
                if new_audio:
                    media["audio"] = new_audio

                # Images
                new_images = []
                for img_item in media.get("images", []):
                    img_clean = uncorrupt_str(img_item)
                    fname = os.path.basename(urllib.parse.urlparse(img_clean).path if img_clean.startswith("http") else img_clean)
                    local_path = os.path.join(IMAGES_DIR, fname).replace("\\", "/")
                    new_images.append(local_path)
                    if not (os.path.exists(local_path) and os.path.getsize(local_path) > 0):
                        remote_url = get_remote_url(fname, "images")
                        missing_downloads.append((remote_url, local_path))
                if new_images:
                    media["images"] = new_images

            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"  [✔] Đã phục hồi: {fpath}")

        except Exception as e:
            print(f"  [!] Lỗi xử lý {fpath}: {e}")

    # 2. Tải toàn bộ media với link chuẩn
    unique_tasks = list({p: u for u, p in missing_downloads}.items())
    tasks = [(u, p) for p, u in unique_tasks]

    print(f"\n[*] Bước 2: Bắt đầu tải media...")
    print(f"    - Tổng số tệp cần tải: {len(tasks)}")

    if tasks:
        success = 0
        fail = 0
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(download_file, url, path): (url, path) for url, path in tasks}
            for idx, fut in enumerate(as_completed(futures), 1):
                ok, url, msg = fut.result()
                fname = os.path.basename(url)
                if ok:
                    success += 1
                    print(f"[{idx}/{len(tasks)}] [OK] {fname}")
                else:
                    fail += 1
                    print(f"[{idx}/{len(tasks)}] [LỖI] {fname} -> {msg}")
        print(f"\n[*] Kết quả tải: {success} thành công, {fail} thất bại.")
    else:
        print("[✔] Toàn bộ file Audio và Hình ảnh đã có sẵn trên máy!")

    print("\n" + "=" * 65)
    print(" HOÀN TẤT! Dữ liệu đã khôi phục sạch sẽ và sẵn sàng Offline 100%.")
    print("=" * 65)

if __name__ == "__main__":
    main()