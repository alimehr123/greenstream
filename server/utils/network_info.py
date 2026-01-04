# server/utils/network_info.py

import socket
from typing import List


DEFAULT_PORT = 8000
FALLBACK_IP = "127.0.0.1"


def _is_port_open(ip: str, port: int, timeout: float = 0.3) -> bool:
    """
    Check whether (ip:port) is in LISTEN state.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        return s.connect_ex((ip, port)) == 0
    except OSError:
        return False
    finally:
        s.close()


def _get_all_local_ips() -> List[str]:
    """
    Collect all IPv4 addresses assigned to this machine.
    """
    ips = set()

    try:
        hostname = socket.gethostname()
        _, _, host_ips = socket.gethostbyname_ex(hostname)
        for ip in host_ips:
            if not ip.startswith("127."):
                ips.add(ip)
    except OSError:
        pass

    # Fallback: detect outbound interface (standard trick)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ips.add(s.getsockname()[0])
        s.close()
    except OSError:
        pass

    return list(ips)


def get_lan_ip(port: int = DEFAULT_PORT) -> str:
    """
    Return the LAN IP where the given port is actually listening.

    Priority:
    1. LAN IPs that have `port` open
    2. 127.0.0.1 if nothing matches
    """
    ips = _get_all_local_ips()

    # Try LAN IPs first
    for ip in ips:
        if _is_port_open(ip, port):
            return ip

    # Fallback to localhost (useful before server fully starts)
    if _is_port_open(FALLBACK_IP, port):
        return FALLBACK_IP

    return FALLBACK_IP


# --------------------------------------------------
# Optional CLI usage (debug / batch support)
# --------------------------------------------------
if __name__ == "__main__":
    print(get_lan_ip())
