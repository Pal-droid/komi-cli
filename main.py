#!/usr/bin/env python3

import sys
import curses
import threading
import subprocess

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text

from config import PROXY_PORT
from scraper import search, find_chapters, find_pages
from reader import generate_html
from server import start_proxy, prefetch_images, prefetch_adjacent, _state, _state_lock, _chapter_html_cache

console = Console()


# -- TUI helpers --------------------------------------------------------------

def tui_header():
    console.print(Panel(
        Text("KOMI-CLI", style="bold red", justify="center"),
        subtitle="[dim]↑↓ navigate · Enter select · q quit[/dim]",
        border_style="red",
        padding=(0, 2),
    ))


def tui_loading(message):
    return Live(
        Spinner("dots", text=f"[dim]{message}[/dim]", style="red"),
        console=console,
        transient=True,
    )


def tui_select(items, label_fn, title, subtitle=None):
    """Arrow-key selection list using curses. Returns (index, item) or (None, None)."""
    labels = [label_fn(item) for item in items]

    def _draw(stdscr, selected):
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        curses.curs_set(0)
        curses.start_color()
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)

        title_str = f" {title} "
        stdscr.attron(curses.color_pair(1) | curses.A_BOLD)
        stdscr.addstr(0, max(0, (w - len(title_str)) // 2), title_str[:w])
        stdscr.attroff(curses.color_pair(1) | curses.A_BOLD)

        if subtitle:
            sub = subtitle[:w-2]
            stdscr.attron(curses.color_pair(2) | curses.A_DIM)
            stdscr.addstr(1, max(0, (w - len(sub)) // 2), sub)
            stdscr.attroff(curses.color_pair(2) | curses.A_DIM)

        list_start = 3
        list_height = h - list_start - 2
        scroll = max(0, selected - list_height // 2)
        scroll = min(scroll, max(0, len(labels) - list_height))

        for i, label in enumerate(labels[scroll:scroll + list_height]):
            real_i = i + scroll
            y = list_start + i
            if y >= h - 2:
                break
            prefix = " ▶ " if real_i == selected else "   "
            line = f"{prefix}{real_i + 1:>3}. {label}"[:w-1]
            if real_i == selected:
                stdscr.attron(curses.color_pair(1) | curses.A_BOLD)
                stdscr.addstr(y, 0, line.ljust(w - 1))
                stdscr.attroff(curses.color_pair(1) | curses.A_BOLD)
            else:
                stdscr.attron(curses.color_pair(2))
                stdscr.addstr(y, 0, line.ljust(w - 1))
                stdscr.attroff(curses.color_pair(2))

        hint = " ↑↓ navigate  Enter select  q quit "
        stdscr.attron(curses.A_DIM)
        stdscr.addstr(h - 1, max(0, (w - len(hint)) // 2), hint[:w])
        stdscr.attroff(curses.A_DIM)

        if len(labels) > list_height:
            bar_h = max(1, list_height * list_height // len(labels))
            bar_y = list_start + scroll * (list_height - bar_h) // max(1, len(labels) - list_height)
            for by in range(list_height):
                char = "█" if bar_y <= by < bar_y + bar_h else "░"
                try:
                    stdscr.addstr(list_start + by, w - 1, char)
                except curses.error:
                    pass

        stdscr.refresh()

    result = [None]

    def _run(stdscr):
        selected = 0
        while True:
            _draw(stdscr, selected)
            key = stdscr.getch()
            if key in (curses.KEY_UP, ord('k')):
                selected = max(0, selected - 1)
            elif key in (curses.KEY_DOWN, ord('j')):
                selected = min(len(labels) - 1, selected + 1)
            elif key in (curses.KEY_PPAGE,):
                selected = max(0, selected - 10)
            elif key in (curses.KEY_NPAGE,):
                selected = min(len(labels) - 1, selected + 10)
            elif key in (curses.KEY_ENTER, ord('\n'), ord('\r')):
                result[0] = selected
                return
            elif key in (ord('q'), ord('Q'), 27):
                return

    curses.wrapper(_run)
    if result[0] is None:
        return None, None
    return result[0], items[result[0]]


def tui_search():
    console.print()
    return Prompt.ask("[bold red]Search manga[/bold red]").strip()


def tui_error(msg):
    console.print(f"\n[bold red]✗[/bold red] [red]{msg}[/red]\n")


def tui_success(msg):
    console.print(f"\n[bold green]✓[/bold green] [white]{msg}[/white]")


# -- Main ---------------------------------------------------------------------

def main():
    console.clear()
    tui_header()

    # search loop — retry on no results or q
    while True:
        query = tui_search()
        if not query:
            sys.exit(0)

        with tui_loading(f"Searching for '{query}'..."):
            results = search(query)

        if not results:
            tui_error(f"No results found for '{query}'. Try again.")
            continue

        console.print(f"\n[dim]Found [bold white]{len(results)}[/bold white] results[/dim]\n")

        _, manga = tui_select(
            results,
            lambda m: m["title"],
            title="Select Manga",
            subtitle=f"Results for: {query}",
        )
        if manga is None:
            console.clear()
            tui_header()
            continue
        break

    console.clear()
    tui_header()
    console.print(f"\n[dim]Selected:[/dim] [bold white]{manga['title']}[/bold white]\n")

    with tui_loading("Fetching chapters..."):
        chapters = find_chapters(manga["id"])

    if not chapters:
        tui_error("No chapters found.")
        sys.exit(1)

    chapter_idx, chapter = tui_select(
        chapters,
        lambda c: c["title"],
        title=manga["title"],
        subtitle=f"{len(chapters)} chapters available",
    )
    if chapter is None:
        sys.exit(0)

    console.clear()
    tui_header()
    console.print(f"\n[dim]Reading:[/dim] [bold white]{manga['title']}[/bold white] [dim]·[/dim] [red]{chapter['title']}[/red]\n")

    with tui_loading("Fetching pages..."):
        pages = find_pages(chapter["id"])

    if not pages:
        tui_error("No pages found.")
        sys.exit(1)

    tui_success(f"{len(pages)} pages found. Starting proxy...")
    threading.Thread(target=prefetch_images, args=(pages,), daemon=True).start()

    html = generate_html(pages, manga["title"], chapter["title"], chapter_idx, len(chapters),
                         chapters=chapters)

    with _state_lock:
        _state["chapters"] = chapters
        _state["current_index"] = chapter_idx
        _state["manga_title"] = manga["title"]
        _chapter_html_cache[chapter_idx] = html

    start_proxy()

    threading.Thread(target=prefetch_adjacent, args=(chapter_idx,), daemon=True).start()
    tui_success("Prefetching adjacent chapters...")

    url = f"http://127.0.0.1:{PROXY_PORT}/"
    tui_success("Opening in Chrome...")
    subprocess.run(["am", "start", "-a", "android.intent.action.VIEW",
                    "-d", url,
                    "-n", "com.android.chrome/com.google.android.apps.chrome.Main"])

    console.print(f"\n[dim]Press [bold white]Enter[/bold white] when done reading...[/dim]")
    input()

    # post-reading menu
    while True:
        console.print("\n[dim]What do you want to do?[/dim]\n")
        console.print("  [bold white][1][/bold white] Choose another chapter")
        console.print("  [bold white][2][/bold white] Search another manga")
        console.print("  [bold white][3][/bold white] Exit")
        choice = Prompt.ask("\n", choices=["1", "2", "3"], default="3")

        if choice == "1":
            chapter_idx, chapter = tui_select(
                chapters,
                lambda c: c["title"],
                title=manga["title"],
                subtitle=f"{len(chapters)} chapters available",
            )
            if chapter is None:
                continue

            console.clear()
            tui_header()
            console.print(f"\n[dim]Reading:[/dim] [bold white]{manga['title']}[/bold white] [dim]·[/dim] [red]{chapter['title']}[/red]\n")

            with tui_loading("Fetching pages..."):
                pages = find_pages(chapter["id"])

            if not pages:
                tui_error("No pages found.")
                continue

            tui_success(f"{len(pages)} pages found.")
            threading.Thread(target=prefetch_images, args=(pages,), daemon=True).start()

            html = generate_html(pages, manga["title"], chapter["title"], chapter_idx, len(chapters),
                                 chapters=chapters)
            with _state_lock:
                _state["current_index"] = chapter_idx
                _chapter_html_cache[chapter_idx] = html

            threading.Thread(target=prefetch_adjacent, args=(chapter_idx,), daemon=True).start()

            url = f"http://127.0.0.1:{PROXY_PORT}/read?idx={chapter_idx}"
            tui_success("Opening in Chrome...")
            subprocess.run(["am", "start", "-a", "android.intent.action.VIEW",
                            "-d", url,
                            "-n", "com.android.chrome/com.google.android.apps.chrome.Main"])

            console.print(f"\n[dim]Press [bold white]Enter[/bold white] when done reading...[/dim]")
            input()

        elif choice == "2":
            main()
            return

        else:
            sys.exit(0)


if __name__ == "__main__":
    main()

