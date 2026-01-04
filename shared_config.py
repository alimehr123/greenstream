import os
import json
import socket
import sys
from typing import Optional

INTERNET_FALLBACK_URL = "http://greenstream.duckdns.org:8000"
CONFIG_FILE_NAME = "config.json"
SCAN_PORT = 8000
SCAN_TIMEOUT = 0.18     # سریع ولی کافی برای WiFi و Windows/Android
MAX_IP_RANGE = 254       # برای 192.168.x.1 تا 254

def _check_tcp(host: str, port: int) -> bool:
    try:
        sock = socket.create_connection((host, port), timeout=SCAN_TIMEOUT)
        sock.close()
        return True
    except Exception:
        return False

def _get_local_subnet() -> Optional[str]:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))        # فقط برای گرفتن IP داخلی، ارتباط واقعی برقرار نمی‌شود
        local_ip = s.getsockname()[0]
        s.close()
        parts = local_ip.split(".")
        return f"{parts[0]}.{parts[1]}.{parts[2]}"
    except Exception:
        return None

def _scan_lan_for_server() -> Optional[str]:
    subnet = _get_local_subnet()
    if not subnet:
        print("LAN: Could not determine local subnet")
        return None

    print(f"LAN: Scanning subnet {subnet}.xxx ...")

    for i in range(1, MAX_IP_RANGE + 1):
        host = f"{subnet}.{i}"
        if _check_tcp(host, SCAN_PORT):
            url = f"http://{host}:{SCAN_PORT}"
            print(f"LAN: Server found at {url}")
            return url

    print("LAN: No server found in subnet")
    return None

def get_base_url() -> str:
    # 1. Environment variable
    env_url = os.environ.get("SERVER_URL")
    if env_url:
        print(f"Config (1) Using ENV URL: {env_url}")
        return env_url

    # 2. local config.json
    if os.path.exists(CONFIG_FILE_NAME):
        try:
            with open(CONFIG_FILE_NAME, "r") as f:
                data = json.load(f)
            cfg = data.get("server_url")
            if cfg and _check_tcp(cfg.replace("http://", "").replace("https://", ""), SCAN_PORT):
                print(f"Config (2) Using config.json URL: {cfg}")
                return cfg
        except Exception as e:
            print(f"Error reading config.json: {e}")

    # 3. LAN auto discovery (desktop + android)
    lan_url = _scan_lan_for_server()
    if lan_url:
        return lan_url

    # 4. Internet fallback
    print(f"Config (5) Internet Fallback: {INTERNET_FALLBACK_URL}")
    return INTERNET_FALLBACK_URL
