"""Build the profile README images from live GitHub data.

Writes assets/terminal-light.svg and assets/terminal-dark.svg.
Needs a GitHub token in GITHUB_TOKEN (the Actions token works).
"""
import json
import math
import os
import urllib.request
from datetime import date
from xml.sax.saxutils import escape

USER = "MaxLikesCode"
OUT = os.path.join(os.path.dirname(__file__), "..", "assets")

ABOUT = [
    ("role", "Full stack developer"),
    ("location", "Hamburg, Germany"),
    ("works on", "Web, mobile, infrastructure, IoT"),
    ("building", "6K Labs, live-streaming widgets (300k+ users)"),
    ("before", "VFX and 3D animation for ARD and ZDF"),
    ("studied", "B.Sc. Computer Science, Hochschule Darmstadt"),
    ("detour", "1.5 years in New Zealand, freelancing"),
]

FIGLET = [
    " _ __ ___   __ _ __  __",
    "| '_ ` _ \\ / _` |\\ \\/ /",
    "| | | | | | (_| | >  < ",
    "|_| |_| |_|\\__,_|/_/\\_\\",
]

MONO = "ui-monospace, 'SF Mono', SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"
SANS = "-apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Helvetica Neue', 'Segoe UI', Helvetica, Arial, sans-serif"

TERM = {
    "light": dict(bg="#FFFFFF", bar="#ECECEC", edge="#D2D2D7", fg="#1D1D1F", muted="#8E8E93", green="#248A3D", shadow=0.18),
    "dark": dict(bg="#1E1E1E", bar="#2E2E2E", edge="#3A3A3C", fg="#F2F2F7", muted="#98989D", green="#30D158", shadow=0.5),
}



def fetch(token):
    query = """query($login: String!) { user(login: $login) { createdAt
      contributionsCollection { contributionCalendar { totalContributions
        weeks { contributionDays { date contributionCount } } } } } }"""
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        user = json.load(r)["data"]["user"]
    cal = user["contributionsCollection"]["contributionCalendar"]
    weeks = [[(d["date"], d["contributionCount"]) for d in w["contributionDays"]] for w in cal["weeks"]]
    days = [d for w in weeks for d in w]

    busiest = max(days, key=lambda d: d[1])
    longest = run = 0
    for _, n in days:
        run = run + 1 if n else 0
        longest = max(longest, run)

    return dict(
        total=cal["totalContributions"],
        weeks=weeks,
        busiest=busiest,
        longest=longest,
        since=user["createdAt"][:4],
    )


def fmt_date(iso):
    return date.fromisoformat(iso).strftime("%-d %b %Y")


def sparkline(weeks, x, baseline, fill, width=6, gap=2, height=15):
    """One bar per week, drawn as shapes so it does not depend on the font."""
    sums = [sum(n for _, n in w) for w in weeks]
    top = max(sums) or 1
    out = []
    for i, s in enumerate(sums):
        h = max(2, math.sqrt(s / top) * height) if s else 1
        op = 1 if s else 0.35
        out.append(f'<rect x="{x + i * (width + gap):.1f}" y="{baseline - h:.1f}" width="{width}" height="{h:.1f}" rx="1" fill="{fill}" opacity="{op}"/>')
    return "".join(out)


def terminal(theme, s):
    c = TERM[theme]
    size, lh, cw = 14, 21, 8.43  # font size, line height, approx mono char width
    prompt = "max@hamburg ~ % "

    # Each block appears together, as if the command had just run.
    blocks = [
        [("prompt", "figlet max")] + [("figlet", line) for line in FIGLET] + [("blank", "")],
        [("prompt", "cat about.txt")] + [("kv", k, v) for k, v in ABOUT] + [("blank", "")],
        [("prompt", "gh stats --last-year")]
        + [
            ("kv", "contributions", f"{s['total']:,}"),
            ("kv", "busiest day", f"{s['busiest'][1]} on {fmt_date(s['busiest'][0])}"),
            ("kv", "longest streak", f"{s['longest']} days"),
            ("kv", "on github since", s["since"]),
            ("spark", None),
            ("blank", ""),
        ],
    ]

    pad, bar_h, margin = 22, 34, 24
    width = 800
    lines = sum(len(b) for b in blocks) + 1
    height = bar_h + pad + lines * lh + pad
    W, H = width + margin * 2, height + margin * 2

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
        f'aria-label="Terminal showing Max\'s profile: full stack developer in Hamburg, {s["total"]:,} contributions in the last year.">',
        f"<title>Max on the command line</title>",
        f'<defs><filter id="sh" x="-10%" y="-10%" width="120%" height="130%"><feDropShadow dx="0" dy="8" stdDeviation="10" flood-color="#000" flood-opacity="{c["shadow"]}"/></filter>'
        f'<clipPath id="win"><rect x="{margin}" y="{margin}" width="{width}" height="{height}" rx="12"/></clipPath></defs>',
        f'<style>text{{font-family:{MONO};font-size:{size}px;white-space:pre}} .t{{font-family:{SANS};font-size:13px;font-weight:600}}</style>',
        f'<g filter="url(#sh)"><rect x="{margin}" y="{margin}" width="{width}" height="{height}" rx="12" fill="{c["bg"]}"/></g>',
        f'<g clip-path="url(#win)"><rect x="{margin}" y="{margin}" width="{width}" height="{bar_h}" fill="{c["bar"]}"/>'
        f'<line x1="{margin}" y1="{margin + bar_h}" x2="{margin + width}" y2="{margin + bar_h}" stroke="{c["edge"]}"/></g>',
        f'<rect x="{margin + .5}" y="{margin + .5}" width="{width - 1}" height="{height - 1}" rx="11.5" fill="none" stroke="{c["edge"]}"/>',
    ]
    for i, col in enumerate(["#FF5F57", "#FEBC2E", "#28C840"]):
        out.append(f'<circle cx="{margin + 20 + i * 20}" cy="{margin + bar_h / 2}" r="6" fill="{col}"/>')
    out.append(f'<text class="t" x="{margin + width / 2}" y="{margin + bar_h / 2 + 4.5}" text-anchor="middle" fill="{c["muted"]}">max@hamburg: ~</text>')

    x = margin + pad
    y = margin + bar_h + pad + size
    t = 0.25
    for block in blocks:
        out.append(f'<g opacity="0"><set attributeName="opacity" to="1" begin="{t:.2f}s" fill="freeze"/>')
        for item in block:
            kind = item[0]
            if kind == "prompt":
                out.append(
                    f'<text x="{x}" y="{y}" xml:space="preserve"><tspan fill="{c["green"]}" font-weight="700">{escape(prompt)}</tspan>'
                    f'<tspan fill="{c["fg"]}">{escape(item[1])}</tspan></text>'
                )
            elif kind == "figlet":
                out.append(f'<text x="{x}" y="{y}" xml:space="preserve" fill="{c["fg"]}">{escape(item[1])}</text>')
            elif kind == "kv":
                out.append(
                    f'<text x="{x}" y="{y}" xml:space="preserve"><tspan fill="{c["muted"]}">{escape(item[1].ljust(16))}</tspan>'
                    f'<tspan fill="{c["fg"]}">{escape(item[2])}</tspan></text>'
                )
            elif kind == "spark":
                out.append(f'<text x="{x}" y="{y}" xml:space="preserve" fill="{c["muted"]}">activity</text>')
                out.append(sparkline(s["weeks"], x + 16 * cw, y + 2, c["green"]))
            y += lh
        out.append("</g>")
        t += 0.7

    cursor_x = x + len(prompt) * cw
    out.append(
        f'<g opacity="0"><set attributeName="opacity" to="1" begin="{t:.2f}s" fill="freeze"/>'
        f'<text x="{x}" y="{y}" xml:space="preserve" fill="{c["green"]}" font-weight="700">{escape(prompt)}</text>'
        f'<rect x="{cursor_x:.1f}" y="{y - size + 1}" width="{cw:.1f}" height="{size + 3}" fill="{c["fg"]}">'
        f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1.1s" repeatCount="indefinite"/></rect></g>'
    )
    out.append("</svg>")
    return "\n".join(out) + "\n"


def main():
    stats = fetch(os.environ["GITHUB_TOKEN"])
    os.makedirs(OUT, exist_ok=True)
    for theme in ("light", "dark"):
        with open(os.path.join(OUT, f"terminal-{theme}.svg"), "w") as f:
            f.write(terminal(theme, stats))
    print(f"{stats['total']} contributions, busiest {stats['busiest']}, longest streak {stats['longest']}")


if __name__ == "__main__":
    main()
