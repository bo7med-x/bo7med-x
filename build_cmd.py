import json
import os
import urllib.request
from datetime import datetime, timezone
from xml.sax.saxutils import escape

USERNAME = "bo7med-x"
TOKEN = os.environ.get("GITHUB_TOKEN", "")


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
    ranked = sorted(totals.items(), key=lambda x: x[1], reverse=True)[:5]
    return [(lang, round((val / total_bytes) * 100, 1)) for lang, val in ranked]


def render_svg(user, repos, langs):
    followers = user.get("followers", 0)
    following = user.get("following", 0)
    repo_count = len(repos)
    stars = sum(r.get("stargazers_count", 0) for r in repos)
    forks = sum(r.get("forks_count", 0) for r in repos)
    synced = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    top_repos = sorted(
        repos,
        key=lambda r: (r.get("stargazers_count", 0), r.get("pushed_at", "")),
        reverse=True,
    )[:5]

    lines = [
        ("Microsoft Windows [Version 10.0.19045.5011]", "#cccccc"),
        ("(c) Microsoft Corporation. All rights reserved.", "#cccccc"),
        ("", "#cccccc"),
        ("C:\\Users\\BO7MEDX> whoami", "#ffffff"),
        ("desktop-bo7medx\\bo7medx  |  Developer / Reverse Engineer / CoD1 Modder", "#cccccc"),
        ("", "#cccccc"),
        ("C:\\Users\\BO7MEDX> systeminfo | findstr /B /C:\"Account\" /C:\"Followers\" /C:\"Public\" /C:\"Total\"", "#ffffff"),
        (f"Account Handle:            @{USERNAME}", "#cccccc"),
        (f"Followers / Following:     {followers} / {following}", "#cccccc"),
        (f"Public Repositories:       {repo_count}", "#cccccc"),
        (f"Total Stars / Forks:       {stars} / {forks}", "#cccccc"),
        (f"Last Sync:                 {synced}", "#888888"),
        ("", "#cccccc"),
        ("C:\\Users\\BO7MEDX> langstat --top", "#ffffff"),
    ]

    if langs:
        for lang, pct in langs:
            filled = round((pct / 100) * 26)
            bar = "#" * filled + "." * (26 - filled)
            lines.append((f"{lang:<16} {pct:>5.1f}%  [{bar}]", "#cccccc"))
    else:
        lines.append(("No language telemetry indexed yet.", "#888888"))

    lines.append(("", "#cccccc"))
    lines.append(("C:\\Users\\BO7MEDX> dir /b C:\\Users\\BO7MEDX\\Projects", "#ffffff"))
    for r in top_repos:
        lang = r.get("language") or "Mixed"
        st = r.get("stargazers_count", 0)
        lines.append((f"{r['name']:<28} [{lang:<12}]  stars:{st}", "#cccccc"))

    lines.append(("", "#cccccc"))
    lines.append(("[CLICK ANYWHERE IN THIS TERMINAL TO LAUNCH INTERACTIVE CMD SESSION]", "#4ec9b0"))

    line_height = 20
    start_y = 62
    height = start_y + (len(lines) * line_height) + 46

    text_elements = []
    for idx, (content, color) in enumerate(lines):
        y = start_y + idx * line_height
        safe = escape(content) if content else "&#160;"
        text_elements.append(
            f'<text x="18" y="{y}" fill="{color}" font-family="Consolas, \'Courier New\', monospace" font-size="14" xml:space="preserve">{safe}</text>'
        )

    prompt_y = start_y + len(lines) * line_height + 6
    text_elements.append(
        f'<text x="18" y="{prompt_y}" fill="#ffffff" font-family="Consolas, \'Courier New\', monospace" font-size="14" xml:space="preserve">C:\\Users\\BO7MEDX&gt; </text>'
    )
    text_elements.append(
        f'<text x="162" y="{prompt_y}" fill="#ffffff" font-family="Consolas, \'Courier New\', monospace" font-size="14">_<animate attributeName="opacity" values="1;0;1" dur="1s" repeatCount="indefinite" /></text>'
    )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="880" height="{height}" viewBox="0 0 880 {height}">
  <rect x="0.5" y="0.5" width="879" height="{height - 1}" fill="#0c0c0c" stroke="#333333" />
  <rect x="1" y="1" width="878" height="32" fill="#1f1f1f" />
  <line x1="1" y1="33" x2="879" y2="33" stroke="#2d2d2d" />
  <rect x="12" y="9" width="18" height="14" fill="#0c0c0c" stroke="#888888" stroke-width="1" />
  <rect x="12" y="9" width="18" height="3" fill="#cccccc" />
  <text x="15" y="20" fill="#cccccc" font-family="Consolas, monospace" font-size="8">C:\\</text>
  <text x="38" y="21" fill="#cccccc" font-family="'Segoe UI', Tahoma, sans-serif" font-size="12">Command Prompt - C:\\Users\\BO7MEDX</text>
  <text x="775" y="21" fill="#cccccc" font-family="Consolas, monospace" font-size="13">&#9472;</text>
  <text x="815" y="21" fill="#cccccc" font-family="Consolas, monospace" font-size="13">&#9744;</text>
  <text x="855" y="21" fill="#cccccc" font-family="Consolas, monospace" font-size="14">&#10005;</text>
  {"".join(text_elements)}
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
