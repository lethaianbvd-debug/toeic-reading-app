"""
fix_all.py: Tự động sửa toàn bộ lỗi font/ký tự lạ (\ufffd) 
và quét tải bù tất cả các file Audio/Hình ảnh bị thiếu trong mọi file đề thi.
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

def clean_text(text):
    """Sửa các ký tự lỗi mã hóa font phổ biến trong đề thi."""
    if not isinstance(text, str):
        return text
    # Sửa ký tự thay thế \ufffd thành dấu nháy đơn '
    text = text.replace("\ufffd", "'")
    # Sửa các lỗi mã hóa mojibake UTF-8 bị đọc nhầm bảng mã
    text = text.replace("â€™", "'").replace("â€œ", '"').replace("â€", '"').replace("â€“", "-").replace("â€”", " - ")
    return text

def clean_obj(obj):
    """Đệ quy làm sạch tất cả chuỗi văn bản trong đối tượng JSON."""
    if isinstance(obj, dict):
        return {k: clean_obj(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_obj(item) for item in obj]
    elif isinstance(obj, str):
        return clean_text(obj)
    return obj

def get_remote_url(path_or_url, media_type="audio"):
    """Khôi phục lại link tải từ server gốc nếu file đã bị đổi tên thành đường dẫn local."""
    if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
        return path_or_url
    
    filename = os.path.basename(path_or_url)
    if media_type == "audio":
        return f"https://hcm.ss.bfcplatform.vn/tart-cos/mock-tests/{filename}"
    else:
        return f"https://hcm.ss.bfcplatform.vn/tart-cos/image/{filename}"

def download_file(url, save_path, retries=3):
    """Tải file với cơ chế tự động thử lại (retry) khi mạng gián đoạn."""
    if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
        return True, url, "Đã có sẵn"
    
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as response, open(save_path, "wb") as out_file:
                out_file.write(response.read())
            if os.path.getsize(save_path) > 0:
                return True, url, "Thành công"
        except Exception as e:
            if attempt == retries:
                return False, url, str(e)
    return False, url, "Lỗi không xác định"

def main():
    print("=" * 60)
    print(" BẮT ĐẦU QUÉT VÀ TỰ ĐỘNG SỬA TOÀN BỘ FILE ĐỀ THI")
    print("=" * 60)

    # 1. Quét tìm tất cả các file JSON đề thi
    candidates = glob.glob("data/*.json") + glob.glob("*.json")
    ignored = {"package.json", "tsconfig.json", "config.json"}
    json_files = [f for f in candidates if os.path.basename(f) not in ignored and not f.endswith("_backup.json")]

    print(f"[*] Tìm thấy {len(json_files)} file: {', '.join(json_files)}")

    missing_downloads = []
    
    # 2. Bước 1: Sửa lỗi font chữ và quét tìm media bị thiếu
    for fpath in json_files:
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Sửa toàn bộ lỗi font ký tự \ufffd
            data = clean_obj(data)

            if isinstance(data, list):
                for q in data:
                    media = q.get("media", {})
                    
                    # Quét Audio
                    new_audio = []
                    for audio_item in media.get("audio", []):
                        fname = os.path.basename(urllib.parse.urlparse(audio_item).path if audio_item.startswith("http") else audio_item)
                        local_path = os.path.join(AUDIO_DIR, fname).replace("\\", "/")
                        new_audio.append(local_path)
                        
                        # Kiểm tra xem file đã có thật sự trên máy chưa
                        if not (os.path.exists(local_path) and os.path.getsize(local_path) > 0):
                            remote_url = get_remote_url(audio_item, "audio")
                            missing_downloads.append((remote_url, local_path))
                    if new_audio:
                        media["audio"] = new_audio

                    # Quét Hình ảnh
                    new_images = []
                    for img_item in media.get("images", []):
                        fname = os.path.basename(urllib.parse.urlparse(img_item).path if img_item.startswith("http") else img_item)
                        local_path = os.path.join(IMAGES_DIR, fname).replace("\\", "/")
                        new_images.append(local_path)
                        
                        # Kiểm tra xem file đã có thật sự trên máy chưa
                        if not (os.path.exists(local_path) and os.path.getsize(local_path) > 0):
                            remote_url = get_remote_url(img_item, "images")
                            missing_downloads.append((remote_url, local_path))
                    if new_images:
                        media["images"] = new_images

            # Ghi lại file JSON đã được sửa sạch font và đồng bộ đường dẫn
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"[✔] Đã sửa lỗi font & đồng bộ: {fpath}")

        except Exception as e:
            print(f"[!] Lỗi xử lý file {fpath}: {e}")

    # 3. Bước 2: Tải bù tất cả các file Audio / Ảnh bị thiếu
    unique_missing = list({p: u for u, p in missing_downloads}.items())
    tasks = [(u, p) for p, u in unique_missing]

    print(f"\n[*] Phát hiện {len(tasks)} tệp âm thanh/hình ảnh còn thiếu trên máy.")

    if tasks:
        print("[*] Đang tiến hành tải bù tự động...")
        success = 0
        fail = 0
        with ThreadPoolExecutor(max_workers=6) as executor:
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
        print(f"\n[*] Kết quả tải bù: {success} thành công, {fail} thất bại.")
    else:
        print("[✔] Tất cả file Audio và Hình ảnh đã có đầy đủ trên máy!")

    print("\n" + "=" * 60)
    print(" HOÀN TẤT! Toàn bộ file đề thi đã chuẩn font và đầy đủ media.")
    print("=" * 60)

if __name__ == "__main__":
    main()