"""考研剧本杀 · 手机访问服务

启动一个静态 HTTP 服务在端口 8080，自动：
- 过滤掉虚拟网卡 / 链路本地地址，只列出真实局域网 IPv4
- 在终端打印 ASCII 二维码，手机扫一下就能打开
- 自动用默认浏览器打开本地地址
"""
from __future__ import annotations

import http.server
import os
import socket
import socketserver
import sys
import threading
import urllib.parse
import webbrowser

PORT = 8080
SUBPATH = "考研剧本杀合集"


def _candidate_ips():
    """候选 IP：从 socket.getaddrinfo + UDP 探测各拿一份，去重。"""
    ips: list[str] = []
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = info[4][0]
            if ip not in ips:
                ips.append(ip)
    except OSError:
        pass
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        if ip in ips:
            ips.remove(ip)
        ips.insert(0, ip)
    except OSError:
        pass
    return ips


def lan_ips():
    """过滤掉 loopback / link-local / 典型虚拟网卡段。"""
    bad_prefixes = (
        "127.",           # loopback
        "169.254.",       # link-local
        "192.168.56.",    # VirtualBox Host-Only
        "192.168.99.",    # Docker Toolbox
        "172.17.", "172.18.", "172.19.", "172.20.",  # Docker bridges
        "172.21.", "172.22.", "172.23.", "172.24.",
        "172.25.", "172.26.", "172.27.", "172.28.",
        "172.29.", "172.30.", "172.31.",
    )
    return [ip for ip in _candidate_ips() if not ip.startswith(bad_prefixes)]


def encode_url(host, port=PORT, subpath=SUBPATH):
    return f"http://{host}:{port}/{urllib.parse.quote(subpath)}/"


def try_print_qr(url: str, save_path: str | None = None):
    try:
        import qrcode
    except ImportError:
        print("(提示: pip install qrcode[pil] 可启用二维码扫码功能)")
        return
    qr = qrcode.QRCode(border=1)
    qr.add_data(url)
    qr.make(fit=True)
    print("扫码直达 (指向下方第一个 IP):")
    qr.print_ascii(invert=True)
    if save_path:
        try:
            qr.make_image().save(save_path)
            print(f"二维码图片已保存: {save_path}")
        except Exception:
            pass


def start_server(port: int):
    handler = http.server.SimpleHTTPRequestHandler
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), handler) as httpd:
        httpd.serve_forever()


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    ips = lan_ips()
    local_url = encode_url("localhost")

    print("=" * 60)
    print("  考研剧本杀 · 手机访问服务 (Mobile Server)")
    print("=" * 60)
    print()
    print("本机访问 (PC 浏览器):")
    print(f"  >>> {local_url}")
    print()
    if ips:
        print("手机访问 (同 Wi-Fi 下，任选其一):")
        for ip in ips:
            print(f"  >>> {encode_url(ip)}")
        print()
        try_print_qr(encode_url(ips[0]), os.path.join(script_dir, "qr.png"))
    else:
        print("[警告] 未检测到可用的局域网 IPv4，手机无法访问。")
        print("        请确认电脑已连接 Wi-Fi / 有线网络。")
    print()
    print("=" * 60)
    print(f"  服务已启动 · 端口 {PORT} · Ctrl+C 停止")
    print("=" * 60)
    print()

    threading.Timer(1.2, lambda: webbrowser.open(local_url)).start()

    try:
        start_server(PORT)
    except KeyboardInterrupt:
        print("\n服务已停止")
    except OSError as e:
        print(f"\n[错误] 启动失败: {e}")
        print(f"       多半是端口 {PORT} 被占用。请关闭占用程序或改端口后重试。")
        input("按回车退出...")


if __name__ == "__main__":
    main()
