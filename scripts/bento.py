"""Builds the bento-grid profile card (bento.svg) from live GitHub data.

Usage: python scripts/bento.py <output.svg>
Runs daily from .github/workflows/bento.yml. Standard library only.
"""
import datetime as dt
import json
import os
import re
import sys
import urllib.request
from xml.sax.saxutils import escape as esc

USER = "KrishSharma1903"
TAGLINE = "I build machine-learning systems that explain their answers and know when they might be wrong."
FOCUS = ["Grounded RAG that refuses instead of making things up",
         "Explainable ML for healthcare",
         "Real-time computer vision on a plain CPU"]
STACK = ["Python", "PyTorch", "TensorFlow", "scikit-learn", "XGBoost", "OpenCV", "YOLOv8", "FAISS",
         "Hugging Face", "SHAP", "Streamlit", "C++", "SQL", "Git"]

BG, TILE, LINE, TEXT, MUTED = "#0b0d12", "#14171f", "#232733", "#eef0f4", "#8a90a0"
ACC = ["#a78bfa", "#2dd4bf", "#fbbf24", "#f472b6"]
SANS = "'Segoe UI', Ubuntu, 'Helvetica Neue', Arial, sans-serif"
MONO = "'JetBrains Mono', Consolas, Menlo, 'DejaVu Sans Mono', monospace"


def fetch(url, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": f"{USER}-profile", **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode()


def contributions():
    """[(date, count), ...] for the last year, oldest first, from the public contribution calendar."""
    html = fetch(f"https://github.com/users/{USER}/contributions", {"X-Requested-With": "XMLHttpRequest"})
    ids = {m[1]: m[0] for m in re.findall(r'data-date="([\d-]+)" id="([^"]+)"', html)}
    counts = {}
    for fid, text in re.findall(r'for="([^"]+)"[^>]*>([^<]+)', html):
        m = re.match(r"(\d+) contribution", text)
        counts[fid] = int(m[1]) if m else 0
    days = sorted((d, counts.get(i, 0)) for i, d in ids.items())
    if len(days) < 300:
        raise SystemExit(f"contribution calendar looks wrong ({len(days)} days)")
    return days


def commit_total():
    headers = {"Accept": "application/vnd.github+json"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    data = json.loads(fetch(f"https://api.github.com/search/commits?q=author:{USER}&per_page=1", headers))
    return data["total_count"]


def wrap(text, n):
    lines, cur = [], ""
    for w in text.split():
        if len(cur) + len(w) + 1 > n:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    return lines + [cur]


def monthbars(days, x0, y0, w, h):
    months = {}
    for d, c in days:
        months[d[:7]] = months.get(d[:7], 0) + c
    keys = sorted(months)[-12:]
    peak = max(months[k] for k in keys) or 1
    slot = w / len(keys)
    bw, base = slot * 0.56, y0 + h
    out = [f'<line x1="{x0}" y1="{base + .5}" x2="{x0 + w}" y2="{base + .5}" stroke="{LINE}"/>']
    for i, k in enumerate(keys):
        v = months[k]
        x = x0 + i * slot + (slot - bw) / 2
        bh = max(3, (h - 20) * v / peak)
        out.append(f'<rect x="{x:.1f}" y="{base - bh:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="4" fill="{ACC[0] if v else LINE}"/>')
        if v:
            out.append(f'<text x="{x + bw / 2:.1f}" y="{base - bh - 7:.1f}" text-anchor="middle" style="font:600 11px {MONO};fill:{TEXT}">{v}</text>')
        label = dt.date.fromisoformat(k + "-01").strftime("%b")
        out.append(f'<text x="{x + bw / 2:.1f}" y="{base + 18}" text-anchor="middle" style="font:500 10.5px {MONO};fill:{MUTED}">{label}</text>')
    return "".join(out)


def build(days, commits):
    counts = [c for _, c in days]
    run = longest = 0
    for c in counts:
        run = run + 1 if c else 0
        longest = max(longest, run)
    stats = [(f"{sum(counts):,}", "contributions", "last 12 months"), (f"{commits:,}", "commits", "all time"),
             (str(sum(1 for c in counts if c)), "active days", "last 12 months"), (str(longest), "day streak", "longest run")]

    W, G = 1000, 14

    def tile(x, y, w, h):
        return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="{TILE}" stroke="{LINE}"/>'

    b = [tile(0, 0, 610, 260),
         f'<text x="32" y="56" style="font:600 12px {MONO};fill:{ACC[0]};letter-spacing:2.5px">HELLO, I\'M</text>',
         f'<text x="30" y="118" style="font:800 56px {SANS};fill:{TEXT}">Krish Sharma</text>']
    for i, l in enumerate(wrap(TAGLINE, 54)):
        b.append(f'<text x="32" y="{160 + i * 26}" style="font:400 18px {SANS};fill:{MUTED}">{esc(l)}</text>')
    b.append('<rect x="32" y="206" width="220" height="32" rx="16" fill="#0f2a1e" stroke="#1f5a3d"/>'
             '<circle cx="50" cy="222" r="4.5" fill="#4ade80"/>'
             f'<text x="62" y="227" style="font:600 12.5px {MONO};fill:#bbf7d0">open to internships</text>')

    x = 610 + G
    b += [tile(x, 0, W - x, 260),
          f'<text x="{x + 28}" y="48" style="font:600 12px {MONO};fill:{ACC[1]};letter-spacing:2.5px">CURRENTLY</text>']
    y = 90
    for f in FOCUS:
        b.append(f'<circle cx="{x + 34}" cy="{y - 5}" r="4" fill="{ACC[1]}"/>')
        for l in wrap(f, 32):
            b.append(f'<text x="{x + 50}" y="{y}" style="font:500 15.5px {SANS};fill:{TEXT}">{esc(l)}</text>')
            y += 22
        y += 18

    y = 260 + G
    sw = (W - 3 * G) / 4
    for i, (num, label, sub) in enumerate(stats):
        x = i * (sw + G)
        b += [tile(x, y, sw, 124),
              f'<text x="{x + 24}" y="{y + 60}" style="font:800 40px {SANS};fill:{ACC[i]}">{num}</text>',
              f'<text x="{x + 24}" y="{y + 86}" style="font:600 14px {SANS};fill:{TEXT}">{label}</text>',
              f'<text x="{x + 24}" y="{y + 106}" style="font:400 12.5px {MONO};fill:{MUTED}">{sub}</text>']

    y2 = y + 124 + G
    b += [tile(0, y2, 610, 204),
          f'<text x="28" y="{y2 + 40}" style="font:600 12px {MONO};fill:{ACC[2]};letter-spacing:2.5px">ACTIVITY</text>',
          monthbars(days, 28, y2 + 58, 554, 108)]

    x = 610 + G
    b += [tile(x, y2, W - x, 204),
          f'<text x="{x + 28}" y="{y2 + 40}" style="font:600 12px {MONO};fill:{ACC[3]};letter-spacing:2.5px">STACK</text>']
    px, py = x + 28, y2 + 58
    for it in STACK:
        pw = 22 + len(it) * 7.1
        if px + pw > W - 24:
            px, py = x + 28, py + 34
        b.append(f'<rect x="{px}" y="{py}" width="{pw}" height="27" rx="13.5" fill="#1c2029" stroke="{LINE}"/>'
                 f'<text x="{px + 10}" y="{py + 18}" style="font:500 13px {SANS};fill:{TEXT}">{esc(it)}</text>')
        px += pw + 8

    H = y2 + 204
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" fill="none">'
            f'<title>Krish Sharma: {", ".join(f"{n} {l}" for n, l, _ in stats)}</title>{"".join(b)}</svg>')


if __name__ == "__main__":
    svg = build(contributions(), commit_total())
    with open(sys.argv[1], "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {sys.argv[1]}")
