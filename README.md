# komi-cli

![Python](https://img.shields.io/badge/python-3.x-blue?style=flat-square&logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/platform-Termux-black?style=flat-square&logo=android&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)
![Source](https://img.shields.io/badge/source-MangaBuddy-red?style=flat-square)

A manga reader for your terminal. Search MangaBuddy from a curses TUI, then read chapters in Chrome through a local proxy with a full-featured reader UI.

<br>

![Preview](https://raw.githubusercontent.com/Pal-droid/komi-cli/refs/heads/main/images/preview.gif)

---

## Reader

![Reader Preview](https://raw.githubusercontent.com/Pal-droid/komi-cli/refs/heads/main/images/prev_reader.jpg)

---

## Requirements

- Android + Termux
- Python 3
- Chrome (`com.android.chrome`)
- [`rich`](https://github.com/Textualize/rich)

---

## Installation

```bash
git clone https://github.com/Pal-droid/komi-cli
cd komi-cli
pip install -r requirements.txt --break-system-packages
python main.py
```

---

## Usage

```bash
python main.py
```

| Key | Action |
|---|---|
| `↑` `↓` or `j` `k` | Navigate list |
| `Enter` | Select |
| `q` / `ESC` | Go back / cancel |
| `Page Up` / `Page Down` | Scroll 10 items at a time |

Once a chapter opens in Chrome, the proxy keeps running in the background. Switch back to Termux and press **Enter** when done to get the post-reading menu — pick another chapter, search a new manga, or exit.

---

## Reader UI

Tap anywhere while reading to show/hide the bars. The top bar has the chapter title, a progress bar, and two buttons — **Ch.** to jump to any chapter, **View** to open settings.

### Settings

| Section | Options |
|---|---|
| Layout | Long Strip · One Page · Dual Page · Dual Strip |
| Fit *(strip only)* | Full Width · Fitted · Overflow · Fit Height |
| Tap to turn *(paged)* | LTR (left = prev) · RTL (left = next) |
| Page order *(dual)* | Left → Right · Right ← Left |

### Paged mode tap zones
```
┌──────────┬──────────┬──────────┐
│          │          │          │
│  ← prev  │  toggle  │  next →  │
│   35%    │  bars    │   35%    │
│          │   30%    │          │
└──────────┴──────────┴──────────┘
```

Settings persist across chapter navigation.

---

## Project Structure

```
komi-cli/
├── config.py       API base URL, headers, proxy port
├── scraper.py      search, find_chapters, find_pages
├── reader.py       HTML/CSS/JS reader page generator
├── server.py       local proxy, image cache, prefetch
└── main.py         TUI (rich + curses) and entry point
```

---

## How It Works

1. The scraper fetches manga/chapter/page data from MangaBuddy via HTML parsing
2. A local proxy starts on `127.0.0.1:18923`
3. The proxy serves the reader at `/read?idx=N` and forwards image requests with the correct `Referer` header (required by the image CDN)
4. All chapter images are downloaded in parallel into memory as soon as you open a chapter
5. Adjacent chapters are prefetched in the background so next/prev is instant

> All image data is held in memory only — nothing is written to disk.

---

## Notes

- If Chrome is not your browser, replace `com.android.chrome/com.google.android.apps.chrome.Main` in `main.py` with your browser's package/activity name
- The proxy port defaults to `18923` — change it in `config.py` if needed
