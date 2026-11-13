# -*- coding: utf-8 -*-
"""
衡垠世界图集 · 本地 HTTP 服务（零依赖，仅 Python 标准库）

用途：解决浏览器在 file:// 下不能 fetch 本地 JSON 的限制。
本网站的数据已经内嵌在 HTML 里，因此**不启动本服务也能完整使用**；
启动服务只是额外提供「直接在浏览器里查看 data/*.json、*.md」的能力，
并为将来的 HTTP 查询接口预留同一端口。
"""
import os
import sys
import socket
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        # 本地只读资料，允许同源 JSON / Markdown 读取；不写库、不联网
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def log_message(self, fmt, *args):
        msg = fmt % args
        if "/api/" in msg:
            return
        sys.stderr.write("  %s\n" % msg)


def pick_port(start=8765):
    for port in range(start, start + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError("8765—8784 端口都被占用了")


def main():
    os.chdir(ROOT)
    port = pick_port()
    url = "http://127.0.0.1:%d/" % port
    print("=" * 62)
    print("  衡垠世界图集 · 本地网站已启动")
    print("=" * 62)
    print("  网址： " + url)
    print("  目录： " + str(ROOT))
    print("")
    print("  · 网站页面： " + url + "衡垠世界图集.html")
    print("  · 统一索引： " + url + "data/world-index.json")
    print("  · 关联关系： " + url + "data/relationships.json")
    print("  · 阅读入口： " + url + "data/AI_START_HERE.md")
    print("")
    print("  按 Ctrl+C 可停止服务。关闭本窗口即关闭网站。")
    print("  说明：网站是纯静态的，不启动服务也可以双击 HTML 直接打开。")
    print("=" * 62)
    if "--no-browser" not in sys.argv:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")


if __name__ == "__main__":
    main()
