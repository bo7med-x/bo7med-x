import json
import os
import urllib.request
from datetime import datetime, timezone
from xml.sax.saxutils import escape

USERNAME = "bo7med-x"
TOKEN = os.environ.get("GITHUB_TOKEN", "")

LANG_COLORS = {
    "Python": "#3b78ff",
    "C": "#61d6d6",
    "C++": "#b4009e",
    "JavaScript": "#f9f1a5",
    "TypeScript": "#3b78ff",
    "HTML": "#e74856",
    "CSS": "#881798",
    "Shell": "#16c60c",
    "PowerShell": "#3a96dd",
    "PHP": "#881798",
    "Batchfile": "#c19c00",
}
FALLBACK_COLORS = ["#16c60c", "#61d6d6", "#f9f1a5", "#b4009e", "#e74856", "#3a96dd"]


def api_get(url):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": USERNAME,
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_repos():
    repos = []
    page = 1
    while True:
        batch = api_get(f"https://api.github.com/users/{USERNAME}/repos?per_page=100&type=owner&page={page}")
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return [r for r in repos if not r.get("fork")]


def get_lang_summary(repos):
    totals = {}
    for r in repos:
        if r.get("name", "").lower() == USERNAME.lower():
            continue
        url = r.get("languages_url")
        if not url:
            continue
        try:
            data = api_get(url)
            for k, v in data.items():
                totals[k] = totals.get(k, 0) + v
        except Exception:
            continue
    total_bytes = sum(totals.values()) or 1
    ranked = sorted(totals.items(), key=lambda x: x[1], reverse=True)[:6]
    result = []
    for idx, (lang, val) in enumerate(ranked):
        pct = round((val / total_bytes) * 100, 1)
        color = LANG_COLORS.get(lang, FALLBACK_COLORS[idx % len(FALLBACK_COLORS)])
        result.append((lang, pct, color))
    return result


def render_svg(user, repos, langs):
    followers = user.get("followers", 0)
    repo_count = len(repos)
    stars = sum(r.get("stargazers_count", 0) for r in repos)
    forks = sum(r.get("forks_count", 0) for r in repos)
    synced = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    top_repos = sorted(
        repos,
        key=lambda r: (r.get("stargazers_count", 0), r.get("pushed_at", "")),
        reverse=True,
    )[:6]

    ascii_logo = [
        " ____   ___ _____ __  __ _____ ____  __  __",
        "| __ ) / _ \\___  |  \\/  | ____|  _ \\ \\ \\/ /",
        "|  _ \\| | | | / /| |\\/| |  _| | | | | \\  / ",
        "| |_) | |_| |/ / | |  | | |___| |_| | /  \\ ",
        "|____/ \\___//_/  |_|  |_|_____|____/ /_/\\_\\",
        "                                           ",
        "   [ COD MODDING // GSC // SERVERS ]       ",
    ]

    info_rows = [
        ("USER", f"desktop-bo7medx\\{USERNAME}", "#16c60c"),
        ("ROLE", "CoD Modder, Mapper & Server Admin", "#f2f2f2"),
        ("WORK", "CoD Mods, Custom Maps & Game Servers", "#61d6d6"),
        ("STACK", "GSC, Python, Basic C++, CoD Radiant", "#f9f1a5"),
        ("REPOS", f"{repo_count} Public Repositories", "#f2f2f2"),
        ("STATS", f"{stars} Stars  |  {forks} Forks  |  {followers} Followers", "#f2f2f2"),
        ("SYNCED", synced, "#767676"),
    ]

    font = "Consolas, 'Lucida Console', 'Courier New', monospace"
    out = []

    out.append(f'<text x="24" y="62" fill="#767676" font-family="{font}" font-size="13">Microsoft Windows [Version 10.0.19045.5011] - Windows Terminal Runtime</text>')
    out.append(f'<text x="24" y="88" fill="#16c60c" font-family="{font}" font-size="14" font-weight="bold">C:\\Users\\BO7MEDX&gt; <tspan fill="#f2f2f2" font-weight="normal">winfetch --telemetry</tspan></text>')

    for idx, art in enumerate(ascii_logo):
        y = 118 + (idx * 19)
        color = "#61d6d6" if idx < 5 else "#3a96dd"
        out.append(f'<text x="24" y="{y}" fill="{color}" font-family="{font}" font-size="13" xml:space="preserve">{escape(art)}</text>')

    out.append('<line x1="418" y1="104" x2="418" y2="242" stroke="#2d2d2d" stroke-width="1" />')

    for idx, (label, val, val_color) in enumerate(info_rows):
        y = 118 + (idx * 19)
        out.append(
            f'<text x="436" y="{y}" font-family="{font}" font-size="13">'
            f'<tspan fill="#3a96dd" font-weight="bold">{label:<7}</tspan>'
            f'<tspan fill="#555555"> : </tspan>'
            f'<tspan fill="{val_color}">{escape(val)}</tspan>'
            f'</text>'
        )

    out.append('<line x1="24" y1="260" x2="876" y2="260" stroke="#222222" stroke-width="1" />')
    out.append(f'<text x="24" y="284" fill="#16c60c" font-family="{font}" font-size="14" font-weight="bold">C:\\Users\\BO7MEDX&gt; <tspan fill="#f2f2f2" font-weight="normal">langstat --distribution</tspan></text>')

    bar_x = 24
    bar_y = 298
    bar_w = 852
    out.append(f'<rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="10" rx="3" fill="#1f1f1f" />')

    if langs:
        total_pct = sum(x[1] for x in langs) or 100
        curr_x = bar_x
        for idx, (lang, pct, color) in enumerate(langs):
            seg_w = round((pct / total_pct) * bar_w)
            if idx == len(langs) - 1:
                seg_w = (bar_x + bar_w) - curr_x
            if seg_w > 0:
                out.append(f'<rect x="{curr_x}" y="{bar_y}" width="{seg_w}" height="10" fill="{color}" />')
                curr_x += seg_w

        legend_y = 328
        lx = 24
        for lang, pct, color in langs:
            out.append(f'<rect x="{lx}" y="{legend_y - 9}" width="9" height="9" rx="2" fill="{color}" />')
            label_txt = f"{lang} {pct:.1f}%"
            out.append(f'<text x="{lx + 15}" y="{legend_y}" fill="#cccccc" font-family="{font}" font-size="12">{escape(label_txt)}</text>')
            lx += max(135, len(label_txt) * 8 + 30)
    else:
        out.append(f'<text x="24" y="328" fill="#767676" font-family="{font}" font-size="12">No language metrics indexed yet.</text>')

    out.append('<line x1="24" y1="346" x2="876" y2="346" stroke="#222222" stroke-width="1" />')
    out.append(f'<text x="24" y="370" fill="#16c60c" font-family="{font}" font-size="14" font-weight="bold">C:\\Users\\BO7MEDX&gt; <tspan fill="#f2f2f2" font-weight="normal">tasklist /v /fi "STATUS eq active"</tspan></text>')

    hy = 396
    out.append(
        f'<text y="{hy}" fill="#61d6d6" font-family="{font}" font-size="13" font-weight="bold">'
        f'<tspan x="24">IMAGE NAME</tspan>'
        f'<tspan x="345">PID</tspan>'
        f'<tspan x="430">LANGUAGE</tspan>'
        f'<tspan x="595">STARS</tspan>'
        f'<tspan x="685">SIZE</tspan>'
        f'<tspan x="780">UPDATED</tspan>'
        f'</text>'
    )
    out.append('<line x1="24" y1="404" x2="876" y2="404" stroke="#333333" stroke-width="1" />')

    row_y = 424
    for idx, r in enumerate(top_repos):
        name = f"{r['name']}.exe"[:34]
        pid = str(1040 + idx * 16)
        lang = (r.get("language") or "Mixed")[:16]
        lang_col = LANG_COLORS.get(lang, "#cccccc")
        st = str(r.get("stargazers_count", 0))
        sz = f"{r.get('size', 0)} KB"
        upd = (r.get("pushed_at") or "")[:10]

        out.append(
            f'<text y="{row_y}" font-family="{font}" font-size="13">'
            f'<tspan x="24" fill="#f2f2f2">{escape(name)}</tspan>'
            f'<tspan x="345" fill="#767676">{pid}</tspan>'
            f'<tspan x="430" fill="{lang_col}">{escape(lang)}</tspan>'
            f'<tspan x="595" fill="#f9f1a5">{st}</tspan>'
            f'<tspan x="685" fill="#cccccc">{sz}</tspan>'
            f'<tspan x="780" fill="#888888">{upd}</tspan>'
            f'</text>'
        )
        row_y += 22

    footer_y = row_y + 18
    height = footer_y + 22

    out.append(f'<line x1="24" y1="{footer_y - 20}" x2="876" y2="{footer_y - 20}" stroke="#222222" stroke-width="1" />')
    out.append(
        f'<text x="24" y="{footer_y}" fill="#16c60c" font-family="{font}" font-size="14" font-weight="bold">C:\\Users\\BO7MEDX&gt; '
        f'<tspan fill="#f2f2f2">&#9608;<animate attributeName="opacity" values="1;0;1" dur="1s" repeatCount="indefinite" /></tspan>'
        f'</text>'
    )
    out.append(
        f'<text x="876" y="{footer_y}" text-anchor="end" fill="#61d6d6" font-family="{font}" font-size="12">'
        f'[ CLICK ANYWHERE TO LAUNCH INTERACTIVE CMD SESSION ]'
        f'</text>'
    )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="900" height="{height}" viewBox="0 0 900 {height}">
  <rect x="0.5" y="0.5" width="899" height="{height - 1}" rx="8" fill="#0c0c0c" stroke="#30363d" />
  <path d="M 1 8 Q 1 1 8 1 L 892 1 Q 899 1 899 8 L 899 36 L 1 36 Z" fill="#181818" />
  <line x1="1" y1="36" x2="899" y2="36" stroke="#2d2d2d" />
  <path d="M 14 36 L 14 12 Q 14 7 19 7 L 285 7 Q 290 7 290 12 L 290 36 Z" fill="#0c0c0c" />
  <rect x="24" y="15" width="16" height="12" rx="1" fill="#0c0c0c" stroke="#61d6d6" stroke-width="1.2" />
  <rect x="24" y="15" width="16" height="3" fill="#61d6d6" />
  <text x="48" y="25" fill="#f2f2f2" font-family="'Segoe UI', Tahoma, sans-serif" font-size="12">Command Prompt - C:\\Users\\BO7MEDX</text>
  <text x="272" y="25" fill="#888888" font-family="Consolas, monospace" font-size="12">&#10005;</text>
  <text x="306" y="25" fill="#888888" font-family="Consolas, monospace" font-size="15">+</text>
  <text x="802" y="24" fill="#cccccc" font-family="Consolas, monospace" font-size="13">&#9472;</text>
  <text x="838" y="24" fill="#cccccc" font-family="Consolas, monospace" font-size="13">&#9744;</text>
  <text x="872" y="24" fill="#e74856" font-family="Consolas, monospace" font-size="14">&#10005;</text>
  {"".join(out)}
</svg>
"""
    with open("cmd.svg", "w", encoding="utf-8") as f:
        f.write(svg)


def main():
    user = api_get(f"https://api.github.com/users/{USERNAME}")
    repos = get_repos()
    langs = get_lang_summary(repos)
    render_svg(user, repos, langs)


if __name__ == "__main__":
    main()
