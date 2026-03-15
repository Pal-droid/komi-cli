import urllib.parse
from config import PROXY_PORT

def generate_html(pages, manga_title, chapter_title, chapter_index, total_chapters, chapters=None,
                  init_layout="long-strip", init_fit="fullscreen", init_tap="ltr", init_dir="ltr"):
    if chapters is None:
        chapters = []
    has_prev = chapter_index > 0
    has_next = chapter_index < total_chapters - 1

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{manga_title} - {chapter_title}</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}

    body {{
      background: #111;
      font-family: -apple-system, sans-serif;
      color: #fff;
      overscroll-behavior: none;
      overflow-x: hidden;
    }}

    /* ── Top bar ── */
    #topbar {{
      position: fixed;
      top: 0; left: 0; right: 0;
      z-index: 110;
      background: linear-gradient(to bottom, rgba(0,0,0,.85), transparent);
      padding: 12px 16px 24px;
      display: flex;
      flex-direction: column;
      gap: 8px;
      transform: translateY(0);
      transition: transform .3s ease;
    }}
    #topbar.hidden {{ transform: translateY(-110%); }}

    #topbar-row {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
    }}

    #chapter-title {{
      font-size: 13px;
      font-weight: 600;
      opacity: .9;
      flex: 1;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}

    #style-btn {{
      background: rgba(255,255,255,.15);
      border: none;
      color: #fff;
      border-radius: 8px;
      padding: 6px 10px;
      font-size: 12px;
      cursor: pointer;
      white-space: nowrap;
      flex-shrink: 0;
    }}

    /* progress bar */
    #progress-wrap {{
      height: 3px;
      background: rgba(255,255,255,.2);
      border-radius: 2px;
      overflow: hidden;
    }}
    #progress-bar {{
      height: 100%;
      background: #e74c3c;
      border-radius: 2px;
      width: 0%;
      transition: width .2s;
    }}

    /* ── Style panel ── */
    #style-panel {{
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      z-index: 200;
      background: rgba(0,0,0,.7);
      display: none;
      align-items: flex-end;
      justify-content: center;
    }}
    #style-panel.open {{ display: flex; }}
    #style-sheet {{
      background: #1e1e1e;
      border-radius: 20px 20px 0 0;
      padding: 20px 16px 36px;
      width: 100%;
      max-width: 480px;
    }}
    #style-sheet h3 {{
      font-size: 14px;
      opacity: .5;
      margin-bottom: 14px;
      text-align: center;
      text-transform: uppercase;
      letter-spacing: 1px;
    }}
    .style-option {{
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 14px 12px;
      border-radius: 12px;
      cursor: pointer;
      transition: background .15s;
    }}
    .style-option:hover, .style-option.active {{ background: rgba(255,255,255,.1); }}
    .style-icon {{ width: 32px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }}
    .style-icon svg {{ width: 20px; height: 20px; stroke: rgba(255,255,255,.7); stroke-width: 1.8; }}
    .style-option.active .style-icon svg {{ stroke: #fff; }}
    .style-label {{ font-size: 15px; font-weight: 500; }}
    .style-desc {{ font-size: 12px; opacity: .5; margin-top: 2px; }}

    /* ── Chapter list panel ── */
    #chapter-panel {{
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      z-index: 200;
      background: rgba(0,0,0,.7);
      display: none;
      align-items: flex-end;
      justify-content: center;
    }}
    #chapter-panel.open {{ display: flex; }}
    #chapter-sheet {{
      background: #1e1e1e;
      border-radius: 20px 20px 0 0;
      width: 100%;
      max-width: 480px;
      max-height: 70vh;
      display: flex;
      flex-direction: column;
    }}
    #chapter-sheet-header {{
      padding: 16px 16px 8px;
      font-size: 14px;
      opacity: .5;
      text-align: center;
      text-transform: uppercase;
      letter-spacing: 1px;
      flex-shrink: 0;
    }}
    #chapter-list {{
      overflow-y: auto;
      padding: 4px 8px 32px;
    }}
    .chapter-item {{
      padding: 12px 10px;
      border-radius: 10px;
      font-size: 14px;
      cursor: pointer;
      transition: background .15s;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .chapter-item:active {{ background: rgba(255,255,255,.1); }}
    .chapter-item.current {{
      background: rgba(231,76,60,.15);
      color: #e74c3c;
      font-weight: 600;
    }}
    .chapter-item .ch-dot {{
      width: 6px; height: 6px;
      border-radius: 50%;
      background: currentColor;
      opacity: .4;
      flex-shrink: 0;
    }}
    .chapter-item.current .ch-dot {{ opacity: 1; }}

    /* ── Bottom bar ── */
    #bottombar {{
      position: fixed;
      bottom: 0; left: 0; right: 0;
      z-index: 110;
      background: linear-gradient(to top, rgba(0,0,0,.85), transparent);
      padding: 24px 16px 20px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      transform: translateY(0);
      transition: transform .3s ease;
    }}
    #bottombar.hidden {{ transform: translateY(110%); }}

    .nav-btn {{
      background: rgba(255,255,255,.12);
      border: none;
      color: #fff;
      border-radius: 12px;
      padding: 10px 18px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      transition: background .15s, opacity .15s;
    }}
    .nav-btn:disabled {{ opacity: .25; cursor: default; }}
    .nav-btn:not(:disabled):active {{ background: rgba(255,255,255,.25); }}

    #page-counter {{
      font-size: 13px;
      opacity: .6;
      flex: 1;
      text-align: center;
    }}

    /* ── Pages ── */
    #reader {{
      display: flex;
      flex-direction: column;
      align-items: center;
      width: 100%;
    }}

    /* ── Tap zones (paged modes) ── */
    #tap-prev, #tap-next {{
      display: none;
      position: fixed;
      top: 60px;
      bottom: 70px;
      width: 35%;
      z-index: 90;
      cursor: pointer;
    }}
    #tap-center {{
      display: none;
      position: fixed;
      top: 60px;
      bottom: 70px;
      left: 35%; right: 35%;
      z-index: 90;
      cursor: pointer;
    }}
    #tap-prev {{ left: 0; }}
    #tap-next {{ right: 0; }}

    /* loading overlay per chapter change */
    #loading {{
      position: fixed;
      inset: 0;
      background: #111;
      z-index: 300;
      display: none;
      align-items: center;
      justify-content: center;
      flex-direction: column;
      gap: 12px;
      font-size: 14px;
      opacity: .9;
    }}
    #loading.show {{ display: flex; }}
    .spinner {{
      width: 32px; height: 32px;
      border: 3px solid rgba(255,255,255,.2);
      border-top-color: #e74c3c;
      border-radius: 50%;
      animation: spin .7s linear infinite;
    }}
    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}

    /* ── Page skeleton ── */
    .page-wrap {{
      position: relative;
      width: 100%;
      display: flex;
      justify-content: center;
    }}
    .page-wrap.loading::before {{
      content: '';
      display: block;
      width: 100%;
      aspect-ratio: 2 / 3;
      background: linear-gradient(90deg, #1e1e1e 25%, #2a2a2a 50%, #1e1e1e 75%);
      background-size: 200% 100%;
      animation: shimmer 1.4s infinite;
    }}
    .page-wrap.loading img {{
      position: absolute;
      top: 0; left: 0;
      width: 100%; height: 100%;
      opacity: 0;
    }}
    .page-wrap:not(.loading) img {{
      opacity: 1;
      transition: opacity .3s ease;
    }}
    .page-wrap.error::before {{
      background: #1a1a1a;
      content: '';
      display: block;
      width: 100%;
      aspect-ratio: 2 / 3;
    }}
    .retry-overlay {{
      display: none;
      position: absolute;
      inset: 0;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 12px;
      color: rgba(255,255,255,.4);
      font-size: 13px;
    }}
    .page-wrap.error .retry-overlay {{
      display: flex;
    }}
    .retry-overlay button {{
      background: rgba(255,255,255,.1);
      border: 1px solid rgba(255,255,255,.2);
      color: #fff;
      border-radius: 10px;
      padding: 8px 20px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
    }}
    .retry-overlay button:active {{
      background: rgba(255,255,255,.2);
    }}
    @keyframes shimmer {{
      0%   {{ background-position: 200% 0; }}
      100% {{ background-position: -200% 0; }}
    }}

    /* ── Layout: Long Strip ── */
    body.layout-strip #reader {{
      display: flex;
      flex-direction: column;
      align-items: center;
      width: 100%;
    }}
    body.layout-strip.fit-fitted #reader .page-wrap {{ width: 100%; max-width: 800px; }}
    body.layout-strip.fit-fullscreen #reader .page-wrap {{ width: 100%; max-width: 100vw; }}
    body.layout-strip.fit-fullscreen #reader .page-wrap img {{ width: 100%; height: auto; display: block; }}
    body.layout-strip.fit-overflow #reader .page-wrap {{ width: 150vw; margin-left: -25vw; max-width: none; }}
    body.layout-strip.fit-height #reader .page-wrap {{ height: 100vh; width: auto; max-width: none; }}
    body.layout-strip.fit-height #reader .page-wrap.loading::before {{ aspect-ratio: unset; height: 100vh; width: 60vw; }}

    /* ── Layout: One Page ── */
    body.layout-paged #reader {{
      width: 100vw;
      height: 100vh;
      overflow: hidden;
      pointer-events: none;
    }}
    body.layout-paged #reader .page-wrap {{
      position: absolute;
      inset: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      max-width: none;
    }}
    body.layout-paged #reader .page-wrap img {{
      max-width: 100vw;
      max-height: 100vh;
      width: auto;
      height: auto;
      object-fit: contain;
    }}
    body.layout-paged #reader .page-wrap.loading::before {{
      width: 60vw;
      height: 100vh;
      aspect-ratio: unset;
    }}

    /* ── Layout: Dual Page ── */
    body.layout-dual-paged #reader {{
      width: 100vw;
      height: 100vh;
      overflow: hidden;
      pointer-events: none;
    }}
    .dual-row {{
      display: flex;
      width: 100vw;
      height: 100vh;
      gap: 0;
    }}
    body.layout-dual-paged .dual-row {{
      position: absolute;
      inset: 0;
    }}
    body.layout-dual-paged .dual-row .page-wrap {{
      flex: 1;
      height: 100vh;
      width: 50vw;
      max-width: 50vw;
      min-width: 0;
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    body.layout-dual-paged .dual-row .page-wrap img {{
      max-width: 50vw;
      max-height: 100vh;
      width: auto;
      height: auto;
      object-fit: contain;
      display: block;
    }}
    body.layout-dual-paged .dual-row .page-wrap.loading::before {{
      width: 48vw;
      height: 90vh;
      aspect-ratio: unset;
    }}
    .empty-slot {{ flex: 1; width: 50vw; max-width: 50vw; height: 100vh; }}

    /* ── Layout: Dual Strip ── */
    body.layout-dual-strip #reader {{
      display: flex;
      flex-direction: column;
      align-items: stretch;
      width: 100%;
    }}
    body.layout-dual-strip .dual-row {{
      width: 100%;
      height: auto;
      align-items: flex-start;
    }}
    body.layout-dual-strip .dual-row .page-wrap {{
      flex: 1;
      min-width: 0;
      align-self: flex-start;
    }}
    body.layout-dual-strip .dual-row .page-wrap img {{
      width: 100%;
      height: auto;
      max-height: none;
      display: block;
    }}
    body.layout-dual-strip .dual-row .page-wrap.loading::before {{
      aspect-ratio: 2 / 3;
    }}
  </style>
</head>
<body class="layout-{init_layout} fit-{init_fit}">

<!-- loading overlay -->
<div id="loading">
  <div class="spinner"></div>
  <span>Loading chapter...</span>
</div>

<!-- top bar -->
<div id="topbar">
  <div id="topbar-row">
    <span id="chapter-title">{manga_title} · {chapter_title}</span>
    <button id="chapter-btn" onclick="openChapterPanel()" style="background:rgba(255,255,255,.15);border:none;color:#fff;border-radius:8px;padding:6px 10px;font-size:12px;cursor:pointer;white-space:nowrap;flex-shrink:0;margin-right:6px;display:flex;align-items:center;gap:5px"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg> Ch.</button>
    <button id="style-btn" onclick="openStylePanel()" style="display:flex;align-items:center;gap:5px"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg> View</button>
  </div>
  <div id="progress-wrap">
    <div id="progress-bar"></div>
  </div>
</div>

<!-- style panel -->
<div id="style-panel" onclick="closeStylePanel(event)">
  <div id="style-sheet">

    <h3>Layout</h3>
    <div class="style-option active" data-layout="long-strip" onclick="setLayout('long-strip')">
      <span class="style-icon"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h3"/><path d="M16 3h3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-3"/><line x1="12" y1="3" x2="12" y2="21"/></svg></span>
      <div><div class="style-label">Long Strip</div><div class="style-desc">Continuous vertical scroll</div></div>
    </div>
    <div class="style-option" data-layout="one-page" onclick="setLayout('one-page')">
      <span class="style-icon"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/></svg></span>
      <div><div class="style-label">One Page</div><div class="style-desc">Single page, tap sides to turn</div></div>
    </div>
    <div class="style-option" data-layout="dual-page" onclick="setLayout('dual-page')">
      <span class="style-icon"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="18" rx="1"/><rect x="14" y="3" width="7" height="18" rx="1"/></svg></span>
      <div><div class="style-label">Dual Page</div><div class="style-desc">Two pages side by side, tap to turn</div></div>
    </div>
    <div class="style-option" data-layout="dual-strip" onclick="setLayout('dual-strip')">
      <span class="style-icon"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg></span>
      <div><div class="style-label">Dual Strip</div><div class="style-desc">Two columns, continuous scroll</div></div>
    </div>

    <div id="fit-section">
      <h3 style="margin-top:4px;">Fit</h3>
      <div class="style-option active" data-fit="fullscreen" onclick="setFit('fullscreen')">
        <span class="style-icon"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 3 21 3 21 9"/><polyline points="9 21 3 21 3 15"/><line x1="21" y1="3" x2="14" y2="10"/><line x1="3" y1="21" x2="10" y2="14"/></svg></span>
        <div><div class="style-label">Full Width</div><div class="style-desc">Fills entire screen width</div></div>
      </div>
      <div class="style-option" data-fit="fitted" onclick="setFit('fitted')">
        <span class="style-icon"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 14 10 14 10 20"/><polyline points="20 10 14 10 14 4"/><line x1="10" y1="14" x2="3" y2="21"/><line x1="21" y1="3" x2="14" y2="10"/></svg></span>
        <div><div class="style-label">Fitted</div><div class="style-desc">Max width 800px, centered</div></div>
      </div>
      <div class="style-option" data-fit="overflow" onclick="setFit('overflow')">
        <span class="style-icon"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><polyline points="18 8 22 12 18 16"/><polyline points="6 8 2 12 6 16"/><line x1="2" y1="12" x2="22" y2="12"/></svg></span>
        <div><div class="style-label">Overflow</div><div class="style-desc">150% width, scroll horizontally</div></div>
      </div>
      <div class="style-option" data-fit="height" onclick="setFit('height')">
        <span class="style-icon"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><polyline points="8 18 12 22 16 18"/><polyline points="8 6 12 2 16 6"/><line x1="12" y1="2" x2="12" y2="22"/></svg></span>
        <div><div class="style-label">Fit Height</div><div class="style-desc">One page per screen height</div></div>
      </div>
    </div>

    <div id="tap-section" style="display:none;">
      <h3 style="margin-top:4px;">Tap to turn</h3>
      <div class="style-option active" data-tap="ltr" onclick="setTap('ltr')">
        <span class="style-icon"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg></span>
        <div><div class="style-label">LTR</div><div class="style-desc">Left side = previous page</div></div>
      </div>
      <div class="style-option" data-tap="rtl" onclick="setTap('rtl')">
        <span class="style-icon"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg></span>
        <div><div class="style-label">RTL</div><div class="style-desc">Left side = next page</div></div>
      </div>
    </div>

    <div id="dir-section" style="display:none;">
      <h3 style="margin-top:4px;">Page order</h3>
      <div class="style-option active" data-dir="ltr" onclick="setDir('ltr')">
        <span class="style-icon"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><polyline points="13 17 18 12 13 7"/><polyline points="6 17 11 12 6 7"/></svg></span>
        <div><div class="style-label">Left to Right</div><div class="style-desc">Western reading order</div></div>
      </div>
      <div class="style-option" data-dir="rtl" onclick="setDir('rtl')">
        <span class="style-icon"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><polyline points="11 17 6 12 11 7"/><polyline points="18 17 13 12 18 7"/></svg></span>
        <div><div class="style-label">Right to Left</div><div class="style-desc">Japanese reading order</div></div>
      </div>
    </div>

  </div>
</div>

<!-- tap zones for single/dual page modes -->
<div id="tap-prev" onclick="handleTapPrev()"></div>
<div id="tap-center" onclick="handleTapCenter()"></div>
<div id="tap-next" onclick="handleTapNext()"></div>

<!-- chapter list panel -->
<div id="chapter-panel" onclick="closeChapterPanel(event)">
  <div id="chapter-sheet">
    <div id="chapter-sheet-header">Chapters</div>
    <div id="chapter-list">
      {chr(10).join(f'<div class="chapter-item{" current" if i == chapter_index else ""}" onclick="goToChapter({i})"><span class="ch-dot"></span>{c["title"]}</div>' for i, c in enumerate(chapters))}
    </div>
  </div>
</div>

<!-- reader -->
<div id="reader"></div>

<!-- bottom bar -->
<div id="bottombar">
  <button class="nav-btn" id="prev-btn" onclick="changeChapter(-1)" {'disabled' if not has_prev else ''}>← Prev</button>
  <span id="page-counter">1 / {len(pages)}</span>
  <button class="nav-btn" id="next-btn" onclick="changeChapter(1)" {'disabled' if not has_next else ''}>Next →</button>
</div>

<script>
  const TOTAL_PAGES = {len(pages)};
  const CHAPTER_INDEX = {chapter_index};
  const ALL_SRCS = [{', '.join(f'"http://127.0.0.1:{PROXY_PORT}/img?url={urllib.parse.quote(p)}"' for p in pages)}];

  let barsVisible = true;
  let hideTimer = null;
  let currentLayout = '{init_layout}';
  let currentFit = '{init_fit}';
  let currentTap = '{init_tap}';
  let currentDir = '{init_dir}';
  let currentPage = 0;      // for single/dual paged modes

  // ── Render ──────────────────────────────────────────────────────────────

  function buildPageWrap(src, idx) {{
    const wrap = document.createElement('div');
    wrap.className = 'page-wrap loading';
    wrap.dataset.src = src;
    const img = document.createElement('img');
    img.className = 'manga-page';
    img.dataset.index = idx;
    img.loading = 'lazy';
    img.onload = () => wrap.classList.remove('loading');
    img.onerror = () => {{ wrap.classList.remove('loading'); wrap.classList.add('error'); }};
    img.src = src;
    const retry = document.createElement('div');
    retry.className = 'retry-overlay';
    retry.innerHTML = '<span>Failed to load</span><button onclick="retryPage(this.closest(\\'.page-wrap\\'))">↻ Retry</button>';
    wrap.appendChild(img);
    wrap.appendChild(retry);
    return wrap;
  }}

  function renderReader() {{
    const reader = document.getElementById('reader');
    reader.innerHTML = '';

    // strip body mode classes
    document.body.className = '';

    if (currentLayout === 'long-strip') {{
      document.body.classList.add('layout-strip');
      document.body.classList.add('fit-' + currentFit);
      document.getElementById('fit-section').style.display = '';
      document.getElementById('tap-section').style.display = 'none';
      document.getElementById('dir-section').style.display = 'none';
      document.getElementById('tap-prev').style.display = 'none';
      document.getElementById('tap-center').style.display = 'none';
      document.getElementById('tap-next').style.display = 'none';
      ALL_SRCS.forEach((src, i) => reader.appendChild(buildPageWrap(src, i)));
      setTimeout(updateProgress, 100);

    }} else if (currentLayout === 'one-page') {{
      document.body.classList.add('layout-paged');
      document.getElementById('fit-section').style.display = 'none';
      document.getElementById('tap-section').style.display = '';
      document.getElementById('dir-section').style.display = 'none';
      document.getElementById('tap-prev').style.display = 'block';
      document.getElementById('tap-center').style.display = 'block';
      document.getElementById('tap-next').style.display = 'block';
      renderPaged();

    }} else if (currentLayout === 'dual-page') {{
      document.body.classList.add('layout-dual-paged');
      document.getElementById('fit-section').style.display = 'none';
      document.getElementById('tap-section').style.display = '';
      document.getElementById('dir-section').style.display = '';
      document.getElementById('tap-prev').style.display = 'block';
      document.getElementById('tap-center').style.display = 'block';
      document.getElementById('tap-next').style.display = 'block';
      renderDualPaged();

    }} else if (currentLayout === 'dual-strip') {{
      document.body.classList.add('layout-dual-strip');
      document.getElementById('fit-section').style.display = 'none';
      document.getElementById('tap-section').style.display = 'none';
      document.getElementById('dir-section').style.display = '';
      document.getElementById('tap-prev').style.display = 'none';
      document.getElementById('tap-center').style.display = 'none';
      document.getElementById('tap-next').style.display = 'none';
      renderDualStrip();
    }}
  }}

  function renderPaged() {{
    const reader = document.getElementById('reader');
    reader.innerHTML = '';
    const src = ALL_SRCS[currentPage];
    reader.appendChild(buildPageWrap(src, currentPage));
    updatePagedCounter();
  }}

  function renderDualPaged() {{
    const reader = document.getElementById('reader');
    reader.innerHTML = '';
    const row = document.createElement('div');
    row.className = 'dual-row';
    const idxA = currentPage;
    const idxB = currentPage + 1;
    const srcs = currentDir === 'ltr'
      ? [ALL_SRCS[idxA], idxB < TOTAL_PAGES ? ALL_SRCS[idxB] : null]
      : [idxB < TOTAL_PAGES ? ALL_SRCS[idxB] : null, ALL_SRCS[idxA]];
    srcs.forEach((src, slot) => {{
      if (src) {{
        row.appendChild(buildPageWrap(src, slot === 0 ? (currentDir==='ltr'?idxA:idxB) : (currentDir==='ltr'?idxB:idxA)));
      }} else {{
        const empty = document.createElement('div');
        empty.className = 'page-wrap empty-slot';
        row.appendChild(empty);
      }}
    }});
    reader.appendChild(row);
    updatePagedCounter();
  }}

  function renderDualStrip() {{
    const reader = document.getElementById('reader');
    reader.innerHTML = '';
    // pair up pages
    for (let i = 0; i < TOTAL_PAGES; i += 2) {{
      const row = document.createElement('div');
      row.className = 'dual-row';
      const idxA = i, idxB = i + 1;
      const srcs = currentDir === 'ltr'
        ? [ALL_SRCS[idxA], idxB < TOTAL_PAGES ? ALL_SRCS[idxB] : null]
        : [idxB < TOTAL_PAGES ? ALL_SRCS[idxB] : null, ALL_SRCS[idxA]];
      srcs.forEach((src, slot) => {{
        if (src) row.appendChild(buildPageWrap(src, slot));
        else {{
          const empty = document.createElement('div');
          empty.className = 'page-wrap empty-slot';
          row.appendChild(empty);
        }}
      }});
      reader.appendChild(row);
    }}
    setTimeout(updateProgress, 100);
  }}

  // ── Paged navigation ─────────────────────────────────────────────────────

  function pageStep() {{
    return (currentLayout === 'dual-page') ? 2 : 1;
  }}

  function goNextPage() {{
    const step = pageStep();
    if (currentPage + step < TOTAL_PAGES) {{
      currentPage += step;
      currentLayout === 'dual-page' ? renderDualPaged() : renderPaged();
    }} else {{
      changeChapter(1);
    }}
  }}

  function goPrevPage() {{
    const step = pageStep();
    if (currentPage - step >= 0) {{
      currentPage -= step;
      currentLayout === 'dual-page' ? renderDualPaged() : renderPaged();
    }} else {{
      changeChapter(-1);
    }}
  }}

  function handleTapPrev() {{
    if (currentTap === 'ltr') goPrevPage(); else goNextPage();
  }}
  function handleTapNext() {{
    if (currentTap === 'ltr') goNextPage(); else goPrevPage();
  }}
  function handleTapCenter() {{
    if (barsVisible) hideBars(); else showBars();
  }}
  function tapPrev() {{ goPrevPage(); }}
  function tapNext() {{ goNextPage(); }}

  // ── Progress / counter ───────────────────────────────────────────────────

  function updatePagedCounter() {{
    const display = currentLayout === 'dual-page'
      ? `${{currentPage + 1}}–${{Math.min(currentPage + 2, TOTAL_PAGES)}} / ${{TOTAL_PAGES}}`
      : `${{currentPage + 1}} / ${{TOTAL_PAGES}}`;
    document.getElementById('page-counter').textContent = display;
    const pct = TOTAL_PAGES <= 1 ? 100 : (currentPage / (TOTAL_PAGES - 1)) * 100;
    document.getElementById('progress-bar').style.width = pct + '%';
  }}

  function updateProgress() {{
    if (currentLayout !== 'long-strip' && currentLayout !== 'dual-strip') return;
    const rows = document.querySelectorAll('#reader > .page-wrap, #reader > .dual-row');
    const scrollY = window.scrollY + window.innerHeight * 0.5;
    let current = 0;
    rows.forEach((el, i) => {{ if (el.offsetTop <= scrollY) current = i; }});
    const totalRows = rows.length;
    const totalUnits = currentLayout === 'dual-strip' ? totalRows * 2 : totalRows;
    const pct = totalRows <= 1 ? 100 : (current / (totalRows - 1)) * 100;
    document.getElementById('progress-bar').style.width = pct + '%';
    const pageNum = currentLayout === 'dual-strip' ? current * 2 + 1 : current + 1;
    document.getElementById('page-counter').textContent = pageNum + ' / ' + TOTAL_PAGES;
  }}

  window.addEventListener('scroll', updateProgress, {{ passive: true }});

  // ── Bars show/hide ───────────────────────────────────────────────────────

  function showBars() {{
    barsVisible = true;
    document.getElementById('topbar').classList.remove('hidden');
    document.getElementById('bottombar').classList.remove('hidden');
    clearTimeout(hideTimer);
    hideTimer = setTimeout(hideBars, 4000);
  }}
  function hideBars() {{
    barsVisible = false;
    document.getElementById('topbar').classList.add('hidden');
    document.getElementById('bottombar').classList.add('hidden');
  }}

  document.getElementById('reader').addEventListener('click', (e) => {{
    if (currentLayout === 'one-page' || currentLayout === 'dual-page') return;
    if (barsVisible) hideBars(); else showBars();
  }});

  hideTimer = setTimeout(hideBars, 3000);

  // ── Settings ─────────────────────────────────────────────────────────────

  function openStylePanel() {{
    document.getElementById('style-panel').classList.add('open');
  }}
  function closeStylePanel(e) {{
    if (e.target === document.getElementById('style-panel'))
      document.getElementById('style-panel').classList.remove('open');
  }}

  function setLayout(layout) {{
    currentLayout = layout;
    currentPage = 0;
    document.querySelectorAll('[data-layout]').forEach(el =>
      el.classList.toggle('active', el.dataset.layout === layout));
    renderReader();
    document.getElementById('style-panel').classList.remove('open');
  }}

  function setFit(fit) {{
    currentFit = fit;
    document.querySelectorAll('[data-fit]').forEach(el =>
      el.classList.toggle('active', el.dataset.fit === fit));
    // re-apply body class for strip mode
    if (currentLayout === 'long-strip') {{
      document.body.className = 'layout-strip fit-' + fit;
    }}
  }}

  function setTap(tap) {{
    currentTap = tap;
    document.querySelectorAll('[data-tap]').forEach(el =>
      el.classList.toggle('active', el.dataset.tap === tap));
  }}

  function setDir(dir) {{
    currentDir = dir;
    document.querySelectorAll('[data-dir]').forEach(el =>
      el.classList.toggle('active', el.dataset.dir === dir));
    renderReader();
  }}

  // ── Retry ────────────────────────────────────────────────────────────────

  function retryPage(wrap) {{
    const src = wrap.dataset.src;
    const img = wrap.querySelector('img');
    wrap.classList.remove('error');
    wrap.classList.add('loading');
    img.src = '';
    img.src = src + '&_t=' + Date.now();
  }}

  // ── Chapter navigation ───────────────────────────────────────────────────

  function settingsParams() {{
    return `layout=${{currentLayout}}&fit=${{currentFit}}&tap=${{currentTap}}&dir=${{currentDir}}`;
  }}

  function changeChapter(dir) {{
    const loading = document.getElementById('loading');
    loading.classList.add('show');
    fetch('/chapter?nav=' + dir + '&current=' + CHAPTER_INDEX + '&' + settingsParams())
      .then(r => r.json())
      .then(data => {{
        if (data.url) window.location.href = data.url;
        else loading.classList.remove('show');
      }})
      .catch(() => loading.classList.remove('show'));
  }}

  function goToChapter(idx) {{
    document.getElementById('chapter-panel').classList.remove('open');
    document.getElementById('loading').classList.add('show');
    window.location.href = `http://127.0.0.1:{PROXY_PORT}/read?idx=${{idx}}&${{settingsParams()}}`;
  }}

  function openChapterPanel() {{
    const panel = document.getElementById('chapter-panel');
    panel.classList.add('open');
    // scroll current chapter into view
    const cur = panel.querySelector('.chapter-item.current');
    if (cur) cur.scrollIntoView({{ block: 'center' }});
  }}

  function closeChapterPanel(e) {{
    if (e.target === document.getElementById('chapter-panel'))
      document.getElementById('chapter-panel').classList.remove('open');
  }}

  // ── Init ─────────────────────────────────────────────────────────────────
  // sync active states in settings panel to match loaded settings
  document.querySelectorAll('[data-layout]').forEach(el =>
    el.classList.toggle('active', el.dataset.layout === currentLayout));
  document.querySelectorAll('[data-fit]').forEach(el =>
    el.classList.toggle('active', el.dataset.fit === currentFit));
  document.querySelectorAll('[data-tap]').forEach(el =>
    el.classList.toggle('active', el.dataset.tap === currentTap));
  document.querySelectorAll('[data-dir]').forEach(el =>
    el.classList.toggle('active', el.dataset.dir === currentDir));
  renderReader();
</script>
</body>
</html>"""

