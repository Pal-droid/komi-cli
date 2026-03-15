import re
import urllib.request
import urllib.parse

from config import API, HEADERS


def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="replace")


def search(query):
    url = f"{API}/search?q={urllib.parse.quote(query)}"
    html = fetch(url)
    pattern = re.compile(r'<div\s+class="book-item">([\s\S]*?)<\/div>\s*<\/div>', re.IGNORECASE)
    results = []
    for m in pattern.finditer(html):
        chunk = m.group(1)
        manga_id = re.search(r'href="\/([^"]+)"', chunk, re.IGNORECASE)
        title = re.search(r'<h3>\s*<a[^>]+title="([^"]+)"', chunk, re.IGNORECASE)
        manga_id = manga_id.group(1) if manga_id else None
        title = title.group(1).strip() if title else (manga_id or "Untitled")
        if manga_id:
            results.append({"id": manga_id, "title": title})
    return results


def find_chapters(manga_id):
    html = fetch(f"{API}/{manga_id}")
    book_id = re.search(r'var\s+bookId\s*=\s*(\d+);', html, re.IGNORECASE)
    if not book_id:
        return []
    book_id = book_id.group(1)
    chapters_html = fetch(f"{API}/api/manga/{book_id}/chapters?source=detail")
    pattern = re.compile(
        r'<li[^>]*>[\s\S]*?<a[^>]+href="([^"]+)"[^>]*>[\s\S]*?<strong[^>]*class="chapter-title"[^>]*>([^<]+)<\/strong>',
        re.IGNORECASE
    )
    chapters = []
    for m in pattern.finditer(chapters_html):
        href = m.group(1).strip()
        title = m.group(2).strip()
        chapter_id = href.lstrip("/")
        num = re.search(r'Chapter\s+([\d.]+)', title, re.IGNORECASE)
        num = num.group(1) if num else "0"
        chapters.append({"id": chapter_id, "title": title, "num": float(num)})
    return sorted(chapters, key=lambda c: c["num"])


def find_pages(chapter_id):
    html = fetch(f"{API}/{chapter_id}")
    match = re.search(r"var\s+chapImages\s*=\s*'([^']+)'", html, re.IGNORECASE)
    if not match:
        return []
    raw = match.group(1).split(",")
    pages = []
    for img in raw:
        img = img.strip()
        if img:
            pages.append(img if img.startswith("http") else f"{API}{img}")
    return pages

