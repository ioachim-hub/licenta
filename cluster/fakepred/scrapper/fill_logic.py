import bs4
from requests_html import HTMLSession

from fakepred.scrapper.model import Entry

total_index: int = 0


def fill_logic(existing_entries: list[Entry]) -> list[Entry]:
    entries: list[Entry] = []
    session = HTMLSession()

    for index, entry in enumerate(existing_entries):
        if index == 100:
            break
        data = session.get(entry.link)

        title = data.html.find("h1")[0].text.encode("utf-8").decode()

        content = bs4.BeautifulSoup(
            data.html.find("#main > div > div.post-content")[0].text
        ).get_text()

        entries.append(
            Entry(
                site=entry.site,
                link=entry.link,
                title=title,
                content=content,
                date=entry.date,
            )
        )
    return entries
