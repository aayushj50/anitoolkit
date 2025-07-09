import xml.etree.ElementTree as ET
import requests
import html
import re
from collections import defaultdict
from datetime import datetime

MAL_BASE = "https://myanimelist.net/anime/"
HEADERS = {
    "User-Agent": "Franchise Tree Viewer"
}
RELATION_TYPES = {"Sequel", "Prequel", "Side story", "Summary", "Alternative version", "Spin-off", "Parent story", "OVA", "Special", "Movie"}

def parse_my_list(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    all_anime = {}

    for anime in root.findall('anime'):
        aid = anime.find('series_animedb_id').text
        all_anime[aid] = anime.find('series_title').text

    return all_anime

def fetch_anime_page(anime_id):
    url = f"{MAL_BASE}{anime_id}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            print(f"⚠️ Failed to fetch: {anime_id}")
            return None
        return response.text
    except Exception as e:
        print(f"⚠️ Exception fetching {anime_id}: {e}")
        return None

def extract_title_and_date(html_text):
    title_match = re.search(r'<title>(.*?) - MyAnimeList.net</title>', html_text)
    title = title_match.group(1).replace(" - MyAnimeList.net", "") if title_match else "Unknown"

    date_match = re.search(r'Premiered:</span>\s*<a.*?>(.*?)</a>', html_text)
    date_str = date_match.group(1).strip() if date_match else "Unknown"
    date_obj = parse_release_date(date_str)
    return html.unescape(title), date_obj

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

def fetch_related_anime(anime_id):
    html_text = fetch_anime_page(anime_id)
    if not html_text:
        return [], "Unknown", None

    related = re.findall(r'<a href="https://myanimelist\.net/anime/(\d+).*?"[^>]*>(.*?)</a>.*?<small>\((.*?)\)</small>', html_text)
    related_entries = [(aid, html.unescape(title), rel) for aid, title, rel in related if rel in RELATION_TYPES]
    title, release = extract_title_and_date(html_text)
    return related_entries, title, release

def resolve_input_to_id(query):
    if query.isdigit():
        return query
    if "myanimelist.net/anime/" in query:
        return re.findall(r'/anime/(\d+)', query)[0]
    search_url = f"https://myanimelist.net/anime.php?q={query.replace(' ', '%20')}"
    response = requests.get(search_url, headers=HEADERS, timeout=10)
    match = re.search(r'<a href="https://myanimelist\.net/anime/(\d+)', response.text)
    return match.group(1) if match else None

def build_franchise_tree(root_id, all_user_ids):
    visited = set()
    entries = {}

    def dfs(aid):
        if aid in visited:
            return
        visited.add(aid)
        related, title, release = fetch_related_anime(aid)
        in_list = aid in all_user_ids
        entries[aid] = (title, release, in_list)

        for rel_id, rel_title, rel_type in related:
            if rel_type in RELATION_TYPES:
                dfs(rel_id)

    dfs(root_id)
    return entries

def generate_html(entries, root_id):
    sorted_entries = sorted(entries.items(), key=lambda x: x[1][1] or datetime.max)

    html_parts = [
        "<html><head><meta charset='utf-8'><title>Franchise Tree</title>",
        "<style>",
        "body { background-color: #121212; color: #e0e0e0; font-family: sans-serif; }",
        ".entry { margin: 8px 0; padding: 6px; border-radius: 6px; }",
        ".missing { background-color: #444400; }",
        ".present { background-color: #222222; }",
        "#search { margin: 10px; padding: 8px; width: 300px; font-size: 16px; }",
        "</style>",
        "<script>",
        "function filter() {",
        "let input = document.getElementById('search');",
        "let filter = input.value.toLowerCase();",
        "let entries = document.getElementsByClassName('entry');",
        "for (let i = 0; i < entries.length; i++) {",
        " let text = entries[i].innerText.toLowerCase();",
        " entries[i].style.display = text.includes(filter) ? '' : 'none';",
        "}",
        "}",
        "</script>",
        "</head><body>",
        "<h1>Anime Franchise Tree</h1>",
        "<input id='search' onkeyup='filter()' placeholder='Search franchise...'><br><br>"
    ]

    for aid, (title, release, in_list) in sorted_entries:
        css_class = "entry present" if in_list else "entry missing"
        status = "✅" if in_list else "❌"
        html_parts.append(f"<div class='{css_class}'><a href='{MAL_BASE}{aid}' target='_blank'>{html.escape(title)}</a> — {format_date(release)} {status}</div>")

    html_parts.append("</body></html>")

    with open("anime_franchise_tree.html", "w", encoding="utf-8") as f:
        f.write('\n'.join(html_parts))

def main(xml_path, query):
    user_list = parse_my_list(xml_path)
    resolved_id = resolve_input_to_id(query)

    if not resolved_id:
        print("❌ Could not resolve input to a MAL anime ID.")
        return

    tree = build_franchise_tree(resolved_id, user_list)
    generate_html(tree, resolved_id)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python anime_franchise_tree.py animelist.xml <anime_id_or_name_or_url>")
    else:
        main(sys.argv[1], ' '.join(sys.argv[2:]))
# Script 3 placeholder
