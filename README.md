# komi-cli

A manga reader for your terminal. Searches and scrapes MangaBuddy, serves chapters through a local proxy, and opens them in Chrome with a full-featured reader UI.

## Requirements

- Python 3
- Chrome installed (`com.android.chrome`)
- `rich` library

```bash
pip install rich --break-system-packages
```

## Installation

```bash
git clone https://github.com/youruser/komi-cli
cd komi-cli
python main.py
```

## Usage

Run the script and use the TUI to navigate:

```bash
python main.py
```

- Type a manga title to search
- Use **↑ ↓** or **j k** to navigate lists
- **Enter** to select, **q** to go back
- **Page Up / Page Down** to scroll fast in long chapter lists

Once a chapter opens in Chrome, the proxy runs in the background serving all pages. When you're done, switch back to Termux and press **Enter** to get the post-reading menu.

## Reader UI

Tap the screen while reading to show/hide the top and bottom bars.

**Top bar**
- Chapter title and progress bar
- **Ch.** — opens the chapter list to jump to any chapter
- **View** — opens the settings panel

**Bottom bar**
- **← Prev / Next →** — navigate between chapters
- Page counter

**Settings panel**

| Section | Options |
|---|---|
| Layout | Long Strip, One Page, Dual Page, Dual Strip |
| Fit (strip only) | Full Width, Fitted, Overflow, Fit Height |
| Tap to turn (paged) | LTR (left = prev), RTL (left = next) |
| Page order (dual) | Left to Right, Right to Left |

**Paged modes (One Page / Dual Page)**
- Tap left 35% — previous page
- Tap center 30% — toggle bars
- Tap right 35% — next page

Settings persist when navigating between chapters.

## Project Structure

```
komi-cli/
├── config.py    — API base URL, headers, proxy port
├── scraper.py   — search, find_chapters, find_pages
├── reader.py    — generates the HTML/CSS/JS reader page
├── server.py    — local HTTP proxy, image cache, chapter prefetch
└── main.py      — TUI (rich + curses) and entry point
```

## How It Works

1. The scraper fetches manga/chapter/page data from MangaBuddy
2. A local proxy server starts on `127.0.0.1:18923`
3. The proxy serves the reader HTML at `/read?idx=N` and forwards image requests with the correct `Referer` header (required by the CDN)
4. Images are prefetched in parallel into memory so pages load instantly
5. Adjacent chapters are prefetched in the background as soon as you open one

## Notes

- All image data is held in memory — nothing is written to disk
- The proxy keeps running until you press Enter in Termux and choose Exit
- If Chrome is not your default browser, edit the `am start` command in `main.py` with your browser's package name
