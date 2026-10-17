import os
import sys
import socket
import threading
import functools
import http.server
import webview

def get_base_dir():
    """Tự động xác định thư mục chứa dữ liệu kể cả khi chạy bằng mã nguồn hay file .exe"""
    if getattr(sys, 'frozen', False):
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass and os.path.exists(os.path.join(meipass, "index.html")):
            return meipass
        exe_dir = os.path.dirname(sys.executable)
        if os.path.exists(os.path.join(exe_dir, "index.html")):
            return exe_dir
        internal_dir = os.path.join(exe_dir, "_internal")
        if os.path.exists(os.path.join(internal_dir, "index.html")):
            return internal_dir
        return meipass or exe_dir
    return os.path.dirname(os.path.abspath(__file__))

def get_free_port():
    """Tìm một cổng mạng ngẫu nhiên chưa bị chiếm dụng"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]

class QuietHTTPHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Tắt log để giữ giao diện console sạch sẽ

def start_local_server(directory, port):
    handler = functools.partial(QuietHTTPHandler, directory=directory)
    httpd = http.server.ThreadingHTTPServer(('127.0.0.1', port), handler)
    httpd.serve_forever()

def start_app():
    base_dir = get_base_dir()
    port = get_free_port()

    # Chạy server ngầm phục vụ toàn bộ ảnh, audio và file JSON
    server_thread = threading.Thread(target=start_local_server, args=(base_dir, port), daemon=True)
    server_thread.start()

    # Mở cửa sổ ứng dụng độc lập
    window = webview.create_window(
        title="AN TOEIC - Luyện Thi TOEIC Thực Chiến",
        url=f"http://127.0.0.1:{port}/index.html",
        width=1320,
        height=880,
        resizable=True,
        min_size=(960, 640)
    )
    webview.start()

if __name__ == "__main__":
    start_app()