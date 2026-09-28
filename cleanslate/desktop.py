"""CleanSlate Native Desktop Application Launcher (pywebview + FastAPI)."""

import os
import sys

# Ensure cleanslate root is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time
import socket
import threading
import webbrowser
import uvicorn
import webview

from cleanslate.web.app import app

APP_PORT = 8765


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def run_uvicorn():
    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=APP_PORT,
        log_level="warning",
        access_log=False,
    )
    server = uvicorn.Server(config)
    server.run()


def main():
    # 1. Start backend server if not already running
    if not is_port_in_use(APP_PORT):
        server_thread = threading.Thread(target=run_uvicorn, daemon=True)
        server_thread.start()
        
        # Wait up to 3 seconds for server to be responsive
        for _ in range(30):
            if is_port_in_use(APP_PORT):
                break
            time.sleep(0.1)

    url = f"http://127.0.0.1:{APP_PORT}"

    # 2. Launch native macOS Cocoa window with WebKit
    try:
        window = webview.create_window(
            title="CleanSlate — Local Footprint Audit",
            url=url,
            width=1240,
            height=860,
            min_size=(960, 640),
            text_select=True,
            zoomable=True,
        )
        # webview.start() blocks until the window is closed by the user
        webview.start(debug=False)
    except Exception as e:
        # Fallback to default browser if native window fails
        print(f"Opening in default browser due to GUI limitation: {e}")
        webbrowser.open(url)
        # Keep process alive until interrupted
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    sys.exit(0)


if __name__ == "__main__":
    main()
