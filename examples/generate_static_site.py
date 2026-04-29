#!/usr/bin/env python3
"""Example: Generate a large static HTML site using Strategy 3 (Templates).

Demonstrates how to build multi-page HTML sites without hitting write_file
truncation by using a data JSON + Jinja-free template rendering.
"""

import json
import os

# ---------------------------------------------------------------------------
# PART 1: Save site data
# ---------------------------------------------------------------------------

def create_site_data():
    return {
        "site": {
            "title": "Kubar Labs",
            "description": "Credit rails for India's 64M MSMEs",
            "base_url": "https://example.com"
        },
        "pages": [
            {
                "slug": "index",
                "title": "Home",
                "heading": "Embedded Credit Marketplace",
                "body": "NavDhan is an API-first credit infrastructure layer..."
            },
            {
                "slug": "about",
                "title": "About",
                "heading": "Why MSME Credit Matters",
                "body": "84% of MSMEs are excluded from formal credit..."
            },
            {
                "slug": "contact",
                "title": "Contact",
                "heading": "Get In Touch",
                "body": "Reach us at hello@example.com"
            }
        ],
        "nav": [
            {"label": "Home", "url": "index.html"},
            {"label": "About", "url": "about.html"},
            {"label": "Contact", "url": "contact.html"}
        ]
    }


def save_site_data(path="/tmp/site_data.json"):
    data = create_site_data()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return path


# ---------------------------------------------------------------------------
# PART 2: Template (compact, using triple-brace placeholders)
# ---------------------------------------------------------------------------

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{{{page_title}}} | {{{site_title}}}</title>
    <meta name="description" content="{{{site_description}}}">
    <style>
        body { font-family: system-ui, sans-serif; max-width: 800px; margin: 0 auto; padding: 2rem; }
        nav { border-bottom: 1px solid #ddd; padding-bottom: 1rem; margin-bottom: 2rem; }
        nav a { margin-right: 1rem; text-decoration: none; color: #333; }
        h1 { font-size: 2rem; color: #1a1a1a; }
        footer { margin-top: 4rem; padding-top: 1rem; border-top: 1px solid #ddd; color: #666; font-size: 0.875rem; }
    </style>
</head>
<body>
    <nav>
        {{{nav_links}}}
    </nav>
    <h1>{{{page_heading}}}</h1>
    <p>{{{page_body}}}</p>
    <footer>
        &copy; 2026 {{{site_title}}}. All rights reserved.
    </footer>
</body>
</html>
"""


def render_nav_links(nav_items, current_slug):
    links = []
    for item in nav_items:
        active = ' style="font-weight:bold;"' if item["url"].replace(".html", "") == current_slug else ""
        links.append(f'<a href="{item["url"]}"{active}>{item["label"]}</a>')
    return "\n".join(links)


# ---------------------------------------------------------------------------
# PART 3: Driver (compact, reads data, renders templates)
# ---------------------------------------------------------------------------

def generate_site(data_path, output_dir="/tmp/static_site"):
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    os.makedirs(output_dir, exist_ok=True)
    site = data["site"]

    for page in data["pages"]:
        context = {
            "site_title": site["title"],
            "site_description": site["description"],
            "page_title": page["title"],
            "page_heading": page["heading"],
            "page_body": page["body"],
            "nav_links": render_nav_links(data["nav"], page["slug"]),
        }

        html = HTML_TEMPLATE
        for key, val in context.items():
            html = html.replace(f"{{{{{key}}}}}", str(val))

        out_path = os.path.join(output_dir, f"{page['slug']}.html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Generated: {out_path} ({len(html)} chars)")

    print(f"\nSite generated in {output_dir}")
    print(f"Open: file://{output_dir}/index.html")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="/tmp/site_data.json")
    parser.add_argument("--out", default="/tmp/static_site")
    args = parser.parse_args()

    if not os.path.exists(args.data):
        save_site_data(args.data)
    generate_site(args.data, args.out)
