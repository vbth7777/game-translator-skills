#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interactive HTML Walkthrough Exporter
Converts Markdown walkthroughs into standalone, interactive Linear-dark HTML guides
with sidebar navigation, clickable image zoom modals, and choice badges.
"""

import os
import sys
import re
import argparse
from pathlib import Path

# Ensure utf-8 stdout on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        :root {{
            --bg-primary: #0b0f19;
            --bg-secondary: #111827;
            --bg-card: #1e293b;
            --border: #334155;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent: #38bdf8;
            --accent-gold: #fbbf24;
            --danger: #ef4444;
            --success: #22c55e;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background: var(--bg-primary);
            color: var(--text-primary);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            line-height: 1.6;
            display: flex;
        }}
        /* Sidebar Navigation */
        #sidebar {{
            width: 320px;
            height: 100vh;
            position: sticky;
            top: 0;
            background: var(--bg-secondary);
            border-right: 1px solid var(--border);
            padding: 24px 16px;
            overflow-y: auto;
            flex-shrink: 0;
        }}
        #sidebar h2 {{
            font-size: 16px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--accent-gold);
            margin-bottom: 16px;
        }}
        #sidebar ul {{ list-style: none; }}
        #sidebar li {{ margin-bottom: 6px; }}
        #sidebar a {{
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 13px;
            display: block;
            padding: 6px 10px;
            border-radius: 6px;
            transition: all 0.2s;
        }}
        #sidebar a:hover {{
            background: rgba(56, 189, 248, 0.1);
            color: var(--accent);
        }}
        /* Main Content */
        #content {{
            flex-grow: 1;
            max-width: 1050px;
            padding: 40px 48px;
            margin: 0 auto;
        }}
        h1 {{ font-size: 28px; color: var(--accent-gold); margin-bottom: 12px; }}
        h2 {{ font-size: 22px; color: var(--accent); margin-top: 36px; margin-bottom: 16px; border-bottom: 1px solid var(--border); padding-bottom: 8px; }}
        h3 {{ font-size: 18px; color: #e2e8f0; margin-top: 24px; margin-bottom: 12px; }}
        h4 {{ font-size: 16px; color: var(--accent-gold); margin-top: 24px; margin-bottom: 10px; }}
        p {{ margin-bottom: 14px; color: #cbd5e1; }}
        blockquote {{
            border-left: 4px solid var(--accent);
            background: rgba(56, 189, 248, 0.05);
            padding: 12px 18px;
            margin: 18px 0;
            border-radius: 0 8px 8px 0;
            font-size: 14px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: var(--bg-card);
            border-radius: 8px;
            overflow: hidden;
            font-size: 14px;
        }}
        th, td {{ padding: 12px 16px; text-align: left; border-bottom: 1px solid var(--border); }}
        th {{ background: #0f172a; color: var(--accent-gold); font-weight: 600; }}
        tr:hover td {{ background: rgba(255, 255, 255, 0.02); }}
        /* Images and Cards */
        .step-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 24px;
            margin: 28px 0;
        }}
        .screenshot-container {{
            margin: 16px 0;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid var(--border);
            cursor: pointer;
        }}
        .screenshot-container img {{
            width: 100%;
            height: auto;
            display: block;
            transition: transform 0.2s;
        }}
        .screenshot-container:hover img {{
            transform: scale(1.01);
        }}
        /* Badges */
        .badge-choice {{
            background: rgba(34, 197, 94, 0.15);
            border: 1px solid var(--success);
            color: #86efac;
            padding: 6px 12px;
            border-radius: 6px;
            display: inline-block;
            margin: 6px 0;
            font-weight: 600;
        }}
        .badge-danger {{
            background: rgba(239, 68, 68, 0.15);
            border: 1px solid var(--danger);
            color: #fca5a5;
            padding: 6px 12px;
            border-radius: 6px;
            display: inline-block;
            margin: 6px 0;
            font-weight: 600;
        }}
    </style>
</head>
<body>
    <nav id="sidebar">
        <h2>📑 MỤC LỤC BƯỚC</h2>
        <ul>
            {toc_items}
        </ul>
    </nav>
    <main id="content">
        {main_content}
    </main>
</body>
</html>
"""


def convert_md_to_html(md_path: Path, html_out: Path):
    content = md_path.read_text(encoding="utf-8", errors="replace")

    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else "Ren'Py Game Walkthrough"

    # Extract headings for TOC
    toc_items = []
    step_matches = list(re.finditer(r'^####\s+(BƯỚC\s+[0-9]+:\s+([^-\n]+))', content, re.MULTILINE))
    for idx, m in enumerate(step_matches, 1):
        full_heading = m.group(1).strip()
        anchor = f"step_{idx:02d}"
        toc_items.append(f'<li><a href="#{anchor}">{full_heading}</a></li>')

    # Simple HTML conversion
    html_body = content
    # Headers
    html_body = re.sub(r'^####\s+(BƯỚC\s+[0-9]+:\s+.*)$', r'<h4 id="step_here">\1</h4>', html_body, flags=re.MULTILINE)
    # Replace id step_here with step_01, step_02...
    for idx in range(1, len(step_matches) + 1):
        html_body = html_body.replace('id="step_here"', f'id="step_{idx:02d}"', 1)

    html_body = re.sub(r'^###\s+(.+)$', r'<h3>\1</h3>', html_body, flags=re.MULTILINE)
    html_body = re.sub(r'^##\s+(.+)$', r'<h2>\1</h2>', html_body, flags=re.MULTILINE)
    html_body = re.sub(r'^#\s+(.+)$', r'<h1>\1</h1>', html_body, flags=re.MULTILINE)

    # Blockquotes
    html_body = re.sub(r'^>\s+(.+)$', r'<blockquote>\1</blockquote>', html_body, flags=re.MULTILINE)

    # Images
    html_body = re.sub(
        r'!\[(.*?)\]\((.*?)\)',
        r'<div class="screenshot-container"><img src="\2" alt="\1" loading="lazy"></div>',
        html_body
    )

    # Choices and warnings badges
    html_body = re.sub(r'\*\*(BẮT BUỘC CHỌN.*?)\*\*', r'<span class="badge-choice">👉 \1</span>', html_body)
    html_body = re.sub(r'\*\*(Cạm bẫy Game Over.*?)\*\*', r'<span class="badge-danger">⚠️ \1</span>', html_body)

    # Wrap markdown lists into paragraphs
    html_body = re.sub(r'\n{2,}', r'</p><p>', html_body)

    final_html = HTML_TEMPLATE.format(
        title=title,
        toc_items="\n".join(toc_items),
        main_content=f"<p>{html_body}</p>"
    )

    html_out.parent.mkdir(parents=True, exist_ok=True)
    html_out.write_text(final_html, encoding="utf-8")
    print(f"✅ Exported interactive HTML guide: {html_out}")


def main():
    parser = argparse.ArgumentParser(description="Convert Markdown walkthrough to interactive HTML.")
    parser.add_argument("md_file", help="Path to input Markdown walkthrough (.md)")
    parser.add_argument("--out", "-o", help="Path to output HTML file")
    args = parser.parse_args()

    md_path = Path(args.md_file).resolve()
    if not md_path.is_file():
        print(f"❌ Error: Not found: {md_path}")
        sys.exit(1)

    out_path = Path(args.out).resolve() if args.out else md_path.with_suffix(".html")
    convert_md_to_html(md_path, out_path)


if __name__ == "__main__":
    main()
