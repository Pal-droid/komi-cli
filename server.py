import re
import json
import threading
import urllib.request
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

from config import API, HEADERS, PROXY_PORT
from scraper import find_pages
from reader import generate_html

# -- Shared state -------------------------------------------------------------

_state = {
    "chapters": [],
    "current_index": 0,
    "manga_title": "",
}
_state_lock = threading.Lock()

# -- Caches -------------------------------------------------------------------

_chapter_html_cache = {}
_prefetch_lock = threading.Lock()
_prefetching = set()

_img_cache = {}
_img_cache_lock = threading.Lock()

# -- Image prefetch -----------------------------------------------------------

def prefetch_images(page_urls):
    def _fetch_one(url):
        with _img_cache_lock:
            if url in _img_cache:
                return
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = resp.read()
                ct = resp.headers.get("Content-Type", "image/jpeg")
            with _img_cache_lock:
                _img_cache[url] = (ct, data)
        except Exception:
            pass

    threads = [threading.Thread(target=_fetch_one, args=(u,), daemon=True) for u in page_urls]
    for t in threads:
        t.start()


def prefetch_adjacent(idx):
    with _state_lock:
        chapters = _state["chapters"]
        total = len(chapters)

    for target in [idx - 1, idx + 1]:
        if target < 0 or target >= total:
            continue
        with _prefetch_lock:
            with _state_lock:
                already = _state.get("pages_cache", {}).get(target)
            if already or target in _prefetching:
                if already:
                    threading.Thread(target=prefetch_images, args=(already,), daemon=True).start()
                continue
            _prefetching.add(target)

        def _do_prefetch(i=target):
            try:
                chapter = chapters[i]
                pages = find_pages(chapter["id"])
                with _state_lock:
                    if "pages_cache" not in _state:
                        _state["pages_cache"] = {}
                    _state["pages_cache"][i] = pages
                prefetch_images(pages)
            finally:
                with _prefetch_lock:
                    _prefetching.discard(i)

        threading.Thread(target=_do_prefetch, daemon=True).start()


# -- Proxy handler ------------------------------------------------------------

class ProxyHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        # redirect / to /read
        if parsed.path == "/":
            with _state_lock:
                idx = _state["current_index"]
            self.send_response(302)
            self.send_header("Location", f"http://127.0.0.1:{PROXY_PORT}/read?idx={idx}")
            self.end_headers()
            return

        # serve chapter reader
        if parsed.path == "/read":
            idx = int(params.get("idx", [0])[0])
            s_layout = params.get("layout", ["long-strip"])[0]
            s_fit    = params.get("fit",    ["fullscreen"])[0]
            s_tap    = params.get("tap",    ["ltr"])[0]
            s_dir    = params.get("dir",    ["ltr"])[0]
            with _state_lock:
                chapters = _state["chapters"]
                manga_title = _state["manga_title"]
            if idx < 0 or idx >= len(chapters):
                self.send_error(404)
                return
            chapter = chapters[idx]
            pages = find_pages(chapter["id"])
            html = generate_html(pages, manga_title, chapter["title"], idx, len(chapters),
                                 chapters=chapters,
                                 init_layout=s_layout, init_fit=s_fit,
                                 init_tap=s_tap, init_dir=s_dir)
            threading.Thread(target=prefetch_images, args=(pages,), daemon=True).start()
            with _state_lock:
                _state["current_index"] = idx
                _chapter_html_cache[idx] = html
            threading.Thread(target=prefetch_adjacent, args=(idx,), daemon=True).start()
            data = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        # chapter nav
        if parsed.path == "/chapter":
            direction = int(params.get("nav", [0])[0])
            current = int(params.get("current", [0])[0])
            new_idx = current + direction
            s_layout = params.get("layout", ["long-strip"])[0]
            s_fit    = params.get("fit",    ["fullscreen"])[0]
            s_tap    = params.get("tap",    ["ltr"])[0]
            s_dir    = params.get("dir",    ["ltr"])[0]
            with _state_lock:
                total = len(_state["chapters"])
            if 0 <= new_idx < total:
                url = (f"http://127.0.0.1:{PROXY_PORT}/read?idx={new_idx}"
                       f"&layout={s_layout}&fit={s_fit}&tap={s_tap}&dir={s_dir}")
                resp_data = json.dumps({"url": url}).encode()
            else:
                resp_data = json.dumps({"url": None}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(resp_data)))
            self.end_headers()
            self.wfile.write(resp_data)
            return

        # proxy images
        img_url = params.get("url", [None])[0]
        if img_url:
            img_url = re.sub(r'&_t=\d+$', '', img_url)
            with _img_cache_lock:
                cached = _img_cache.get(img_url)
            if cached:
                ct, data = cached
                self.send_response(200)
                self.send_header("Content-Type", ct)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            try:
                req = urllib.request.Request(img_url, headers=HEADERS)
                with urllib.request.urlopen(req, timeout=20) as resp:
                    data = resp.read()
                    ct = resp.headers.get("Content-Type", "image/jpeg")
                with _img_cache_lock:
                    _img_cache[img_url] = (ct, data)
                self.send_response(200)
                self.send_header("Content-Type", ct)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            except Exception as e:
                self.send_error(502, str(e))
            return

        self.send_error(404)


_proxy_started = False

def start_proxy():
    global _proxy_started
    if _proxy_started:
        return
    server = HTTPServer(("127.0.0.1", PROXY_PORT), ProxyHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    _proxy_started = True

