import xml.etree.ElementTree as ET
import requests
from collections import defaultdict
import os
import html

MAL_BASE = "https://myanimelist.net/anime/"
OUTPUT_FILE = "checked_missing_anime_mal.html"

HEADERS = {
    "User-Agent": "MAL Related Checker"
}

RELATION_TYPES = {"Sequel", "Prequel", "Side story", "Summary", "Alternative version", "Spin-off", "Parent story", "OVA", "Special", "Movie"}

def parse_my_list(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    all_anime = {}
    status_map = {}

    for anime in root.findall('anime'):
        anime_id = anime.find('series_animedb_id').text
        title = anime.find('series_title').text
        status = anime.find('my_status').text
        all_anime[anime_id] = title
        status_map[anime_id] = status

    return all_anime, status_map

def fetch_related_anime(anime_id):
    url = f"{MAL_BASE}{anime_id}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            print(f"⚠️ Failed to fetch: {anime_id}")
            return []
        html_text = response.text

        import re
        related = re.findall(r'<a href="https://myanimelist\.net/anime/(\d+).*?"[^>]*>(.*?)</a>.*?<small>\((.*?)\)</small>', html_text)
        return [(aid, html.unescape(title), relation) for aid, title, relation in related if relation in RELATION_TYPES]
    except Exception as e:
        print(f"⚠️ Exception fetching {anime_id}: {e}")
        return []

def generate_html(groups):
    html_parts = [
        "<html><head><meta charset='utf-8'><title>Check Missing Anime</title>",
        "<style>",
        "body { background-color: #121212; color: #e0e0e0; font-family: sans-serif; }",
        ".franchise { margin-bottom: 30px; padding: 10px; border: 1px solid #444; border-radius: 8px; }",
        ".missing { background-color: #444400; padding: 2px 6px; border-radius: 4px; }",
        "input[type='checkbox'] { transform: scale(1.3); margin-right: 8px; }",
        "#search { margin: 10px; padding: 8px; width: 300px; font-size: 16px; }",
        "</style>",
        "<script>",
        "function filter() {",
        "  var input = document.getElementById('search');",
        "  var filter = input.value.toLowerCase();",
        "  var items = document.getElementsByClassName('franchise');",
        "  for (let i = 0; i < items.length; i++) {",
        "    let txt = items[i].innerText.toLowerCase();",
        "    items[i].style.display = txt.includes(filter) ? '' : 'none';",
        "  }",
        "}",
        "</script></head><body>",
        "<h1>Check Missing Anime</h1>",
        "<input id='search' onkeyup='filter()' placeholder='Search franchises...'><br><br>"
    ]

    for status, franchises in groups.items():
        html_parts.append(f"<h2>{status}</h2>")
        for franchise, entries in franchises.items():
            html_parts.append("<div class='franchise'>")
            html_parts.append(f"<strong>{franchise}</strong><br>")
            for entry in entries:
                aid, title, added = entry
                mark = "class='missing'" if not added else ""
                checkbox = f"<input type='checkbox' {'checked' if added else ''}>"
                html_parts.append(f"{checkbox}<a href='{MAL_BASE}{aid}' target='_blank' {mark}>{html.escape(title)}</a><br>")
            html_parts.append("</div>")

    html_parts.append("</body></html>")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write('\n'.join(html_parts))

def main(xml_path):
    user_anime, status_map = parse_my_list(xml_path)
    grouped = defaultdict(lambda: defaultdict(list))  # {status: {franchise: [entries]}}

    seen = set()

    for aid in user_anime:
        if aid in seen:
            continue
        related = fetch_related_anime(aid)
        all_ids = set([aid] + [r[0] for r in related])
        franchise_id = min(all_ids, key=int)
        franchise_title = user_anime.get(franchise_id, related[0][1] if related else user_anime[aid])
        status = status_map[aid]
        seen.update(all_ids)

        for rel_aid, title, _ in [(aid, user_anime.get(aid, "Unknown"), None)] + related:
            already_added = rel_aid in user_anime
            grouped[status][franchise_title].append((rel_aid, title, already_added))

    generate_html(grouped)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python check_missing_anime_mal.py animelist.xml")
    else:
        main(sys.argv[1])
# Script 1 placeholder
