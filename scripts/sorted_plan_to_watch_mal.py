import xml.etree.ElementTree as ET
import requests
from collections import defaultdict
from datetime import datetime
import html

MAL_BASE = "https://myanimelist.net/anime/"
OUTPUT_HTML = "sorted_plan_to_watch_mal.html"
OUTPUT_TXT = "sorted_plan_to_watch_mal.txt"

HEADERS = {
    "User-Agent": "MAL Plan to Watch Sorter"
}

RELATION_TYPES = {"Sequel", "Prequel", "Side story", "Summary", "Alternative version", "Spin-off", "Parent story", "OVA", "Special", "Movie"}

def parse_my_list(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    plan_to_watch = set()
    all_anime = {}

    for anime in root.findall('anime'):
        aid = anime.find('series_animedb_id').text
        title = anime.find('series_title').text
        status = anime.find('my_status').text
        all_anime[aid] = title
        if status == "Plan to Watch":
            plan_to_watch.add(aid)

    return plan_to_watch, all_anime

def fetch_related(anime_id):
    url = f"{MAL_BASE}{anime_id}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            print(f"⚠️ Failed to fetch: {anime_id}")
            return [], "Unknown", None
        html_text = response.text

        import re
        title_match = re.search(r'<title>(.*?) - MyAnimeList.net</title>', html_text)
        title = title_match.group(1).replace(" - MyAnimeList.net", "") if title_match else "Unknown"

        date_match = re.search(r'Premiered:</span>\s*<a.*?>(.*?)</a>', html_text)
        date_str = date_match.group(1).strip() if date_match else "Unknown"
        release = parse_release_date(date_str)

        related = re.findall(r'<a href="https://myanimelist\.net/anime/(\d+).*?"[^>]*>(.*?)</a>.*?<small>\((.*?)\)</small>', html_text)
        rel_list = [(aid, html.unescape(title), rel) for aid, title, rel in related if rel in RELATION_TYPES]

        return rel_list, title, release
    except Exception as e:
        print(f"⚠️ Exception fetching {anime_id}: {e}")
        return [], "Unknown", None

def parse_release_date(premiered_str):
    try:
        parts = premiered_str.split()
        if len(parts) == 2:
            season, year = parts
            month = {
                "Winter": "01",
                "Spring": "04",
                "Summer": "07",
                "Fall": "10"
            }.get(season, "01")
            return datetime.strptime(f"{year}-{month}-01", "%Y-%m-%d")
        elif len(parts) == 1 and parts[0].isdigit():
            return datetime.strptime(f"{parts[0]}-01-01", "%Y-%m-%d")
    except:
        pass
    return None

def format_date(dt):
    return dt.strftime("%d %B %Y") if dt else "Unknown"

def generate_html(franchises):
    html_parts = [
        "<html><head><meta charset='utf-8'><title>Sorted Plan to Watch</title>",
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
        "<h1>Sorted Plan to Watch</h1>",
        "<input id='search' onkeyup='filter()' placeholder='Search franchises...'><br><br>"
    ]

    for franchise, entries in franchises.items():
        html_parts.append("<div class='franchise'>")
        html_parts.append(f"<strong>{franchise}</strong><br>")
        for entry in entries:
            aid, title, release, in_list = entry
            mark = "class='missing'" if not in_list else ""
            checkbox = f"<input type='checkbox' {'checked' if in_list else ''}>"
            html_parts.append(f"{checkbox}<a href='{MAL_BASE}{aid}' target='_blank' {mark}>{html.escape(title)}</a> — {format_date(release)}<br>")
        html_parts.append("</div>")

    html_parts.append("</body></html>")

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write('\n'.join(html_parts))

def generate_txt(franchises):
    with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
        for franchise, entries in franchises.items():
            f.write(f"{franchise}\n")
            for entry in entries:
                aid, title, release, in_list = entry
                mark = "[✔]" if in_list else "[ ]"
                f.write(f"  {mark} {title} — {format_date(release)}\n")
            f.write("\n")

def main(xml_path):
    ptw_ids, all_entries = parse_my_list(xml_path)
    franchises = {}
    seen_ids = set()

    for aid in ptw_ids:
        if aid in seen_ids:
            continue

        related, title, release = fetch_related(aid)
        all_ids = set([aid] + [r[0] for r in related])
        franchise_id = min(all_ids, key=int)
        franchise_name = all_entries.get(franchise_id, title)
        seen_ids.update(all_ids)

        entries = []
        for rel_aid, rel_title, _ in [(aid, title, None)] + related:
            rel_rel, _, rel_date = fetch_related(rel_aid)
            in_list = rel_aid in all_entries
            entries.append((rel_aid, rel_title, rel_date, in_list))

        sorted_entries = sorted(entries, key=lambda x: x[2] or datetime.max)
        franchises[franchise_name] = sorted_entries

    generate_html(franchises)
    generate_txt(franchises)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python sorted_plan_to_watch_mal.py animelist.xml")
    else:
        main(sys.argv[1])
# Script 2 placeholder
