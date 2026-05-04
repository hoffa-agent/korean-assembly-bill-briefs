#!/usr/bin/env python3
"""Fetch official National Assembly plenary-result notices and create a compact English digest.

No LLM/API key is required: the official source is already in English. The script extracts
headline bullets and item sections, then creates short deterministic summaries for the site.
"""
from __future__ import annotations
import json, re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE = "https://korea.assembly.go.kr:447"
LIST_URL = f"{BASE}/portalEn/bbs/B0000170/list.do?menuNo=1500099"
OUT = Path("data/bills.json")
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; korean-assembly-bill-briefs/1.0)"}

@dataclass
class Item:
    title: str
    summary: str

@dataclass
class BillNotice:
    title: str
    date: str
    url: str
    summary: str
    key_points: list[str]
    items: list[Item]

def clean(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def first_sentences(text: str, max_sentences=2, max_chars=360) -> str:
    text = clean(re.sub(r"^[▲\-\s]+", "", text))
    bits = re.split(r"(?<=[.!?])\s+", text)
    out = " ".join(bits[:max_sentences]).strip()
    if len(out) > max_chars:
        out = out[:max_chars].rsplit(" ", 1)[0] + "…"
    return out

def get_soup(url: str) -> BeautifulSoup:
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")

def parse_list(limit=8) -> list[tuple[str, str, str]]:
    soup = get_soup(LIST_URL)
    links = []
    for a in soup.select('a[href*="/portalEn/bbs/B0000170/view.do"]'):
        title = clean(a.get_text(" "))
        href = urljoin(BASE, a.get("href"))
        if not title or any(href == seen[2] for seen in links):
            continue
        row_text = clean(a.find_parent().get_text(" ") if a.find_parent() else "")
        m = re.search(r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{2}, \d{4}", row_text)
        date = m.group(0) if m else ""
        links.append((title, date, href))
        if len(links) >= limit:
            break
    return links

def parse_notice(title: str, date: str, url: str) -> BillNotice:
    soup = get_soup(url)
    content = soup.select_one(".view_cont, .bbs_view, .board_view, article") or soup.body
    text = clean(content.get_text("\n")) if content else clean(soup.get_text("\n"))
    lines = [clean(x) for x in text.splitlines() if clean(x)]

    # Top bullets usually appear before the prose and are the best high-level digest.
    bullets = []
    for line in lines:
        if line.startswith("-") or line.startswith("ㆍ"):
            point = clean(line.lstrip("-ㆍ "))
            if len(point) > 20 and point not in bullets:
                bullets.append(first_sentences(point, 1, 220))
        if line.startswith("The National Assembly") and bullets:
            break
    bullets = bullets[:7]

    # Extract numbered/key item sections like <1> Amendment to...
    items: list[Item] = []
    matches = list(re.finditer(r"<\d+>\s*([^\n]+)", text))
    for i, m in enumerate(matches[:8]):
        item_title = clean(m.group(1))
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = clean(text[start:end])
        if item_title and body:
            items.append(Item(item_title, first_sentences(body, 2, 420)))

    if bullets:
        summary = "The plenary approved measures covering " + "; ".join(p[0].lower() + p[1:] for p in bullets[:3]) + "."
    elif items:
        summary = "The plenary approved several agenda items, including " + ", ".join(i.title for i in items[:3]) + "."
    else:
        summary = first_sentences(text, 2, 420) or title

    return BillNotice(title=title, date=date, url=url, summary=summary, key_points=bullets, items=items)

def main() -> None:
    notices = []
    for title, date, url in parse_list():
        try:
            notices.append(parse_notice(title, date, url))
        except Exception as exc:
            notices.append(BillNotice(title, date, url, f"Fetch failed for this notice: {exc}", [], []))
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": LIST_URL,
        "bills": [asdict(n) for n in notices],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUT} with {len(notices)} notices")

if __name__ == "__main__":
    main()
