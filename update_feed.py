import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from html import escape

RSS_URL = "https://www.warwickshire.gov.uk/rss/news"

KEYWORDS = [
 "roadwork",
    "roadworks",
    "road closure",
    "road closed",
    "temporary road closure",
    "resurfacing",
    "carriageway resurfacing",
    "footway resurfacing",
    "surface dressing",
    "temporary traffic lights",
    "temporary signals",
    "traffic management",
    "gritting",
    "gritter",
    "gritting route",
    "winter service",
]



PRIORITY_KEYWORDS = [
    "coleshill",
    "b46",
    "b4114",
    "b4117",
    "north warwickshire",
]

OUTPUT_FILE = "feed.xml"


def download(url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "WarwickshireHighwaysRSS/1.0"}
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def text_of(element, tag):
    child = element.find(tag)
    if child is None or child.text is None:
        return ""
    return child.text.strip()


def is_highways_item(title, description):
    text = f"{title} {description}".lower()
    return any(keyword in text for keyword in KEYWORDS)


def priority_score(title, description):
    title_text = title.lower()
    full_text = f"{title} {description}".lower()

    score = 0

    for keyword in PRIORITY_KEYWORDS:
        if keyword in title_text:
            score += 10
        elif keyword in full_text:
            score += 5

    return score

def build_feed():
    source = download(RSS_URL)
    source_root = ET.fromstring(source)

    items = []

    for item in source_root.findall(".//item"):
        title = text_of(item, "title")
        description = text_of(item, "description")
        link = text_of(item, "link")
        pub_date = text_of(item, "pubDate")

        if is_highways_item(title, description):
            items.append({
                "title": title,
                "description": description,
                "link": link,
                "pubDate": pub_date,
                "priority": priority_score(title, description),
            })

    items.sort(key=lambda x: x["priority"], reverse=True)

    now = datetime.now(timezone.utc).strftime(
        "%a, %d %b %Y %H:%M:%S +0000"
    )

    output = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0">',
        '<channel>',
        '<title>Warwickshire Highways &amp; Gritting</title>',
        '<link>https://www.warwickshire.gov.uk/roadworks</link>',
        (
            '<description>'
            'Warwickshire roadworks, road closures, resurfacing, '
            'highways and gritting updates. Coleshill and B46 '
            'items are prioritised.'
            '</description>'
        ),
        '<language>en-gb</language>',
        f'<lastBuildDate>{now}</lastBuildDate>',
    ]

    for item in items:
        output.extend([
            '<item>',
            f'<title>{escape(item["title"])}</title>',
            f'<link>{escape(item["link"])}</link>',
            f'<guid>{escape(item["link"])}</guid>',
            f'<description>{escape(item["description"])}</description>',
        ])

        if item["pubDate"]:
            output.append(
                f'<pubDate>{escape(item["pubDate"])}</pubDate>'
            )

        output.append('</item>')

    output.extend([
        '</channel>',
        '</rss>',
    ])

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        file.write("\n".join(output))

    print(f"Created {OUTPUT_FILE} with {len(items)} highways items.")


if __name__ == "__main__":
    build_feed()
