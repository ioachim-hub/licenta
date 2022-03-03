import xmltodict

import bs4
import pandas as pd
from requests_html import HTMLSession

from licenta_code.scrapper.model import Entry
from licenta_code.scrapper.common import get_driver

total_index: int = 0


driver = get_driver()


def rss_logic(url: str, existing_entries: list[Entry]) -> list[Entry]:
    entries: list[Entry] = []
    session = HTMLSession()

    links = [entry.link for entry in existing_entries]

    data = session.get(url)

    root = xmltodict.parse(str(data.html.raw_html, encoding="utf-8"))

    for item in root["rss"]["channel"]["item"]:
        if item["link"] not in links:
            entries.append(
                Entry(
                    site=url,
                    link=item["link"],
                    title=item["title"],
                    content=bs4.BeautifulSoup(item["content:encoded"]).get_text(),
                    date=pd.to_datetime(item["pubDate"]),
                )
            )
    return entries
