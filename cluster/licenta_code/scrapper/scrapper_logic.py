import pandas as pd

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions


from requests_html import HTMLSession

from licenta_code.scrapper.model import Entry
from licenta_code.scrapper.common import get_driver
from licenta_code.scrapper.common import convert_date

total_index: int = 0


driver = get_driver()


def scrapper_logic(
    url: str, route: str, page: int, date_date: pd.Timestamp
) -> list[Entry]:
    entries: list[Entry] = []
    print(f"scrapping from: {url}{route}page/{page})")

    driver.get(f"{url}{route}page/{page}")

    articles = WebDriverWait(driver, 3).until(
        expected_conditions.presence_of_all_elements_located(
            (By.CSS_SELECTOR, 'article[class^="article-box"]')
        )
    )

    dates = []
    links = []

    for idx in range(len(articles)):
        elems_links = articles[idx].find_elements_by_css_selector("span + a")
        elems_dates = articles[idx].find_elements_by_class_name("date")
        dates.extend([el.text for el in elems_dates])
        links.extend([el.get_attribute("href") for el in elems_links])

    session = HTMLSession()
    for link, date in zip(links, dates):
        data = session.get(link)

        title = data.html.find("h1")[0].text.encode("utf-8").decode()
        content = ""
        for paragraph in data.html.find('div[class^="content-container"] > p'):
            if "class" not in paragraph.attrs:
                content += paragraph.text.encode("utf-8").decode()
        date_entry = pd.to_datetime(convert_date(date), format="%d %m %Y")
        if date_entry == date_date:
            continue
        entries.append(
            Entry(
                site=url,
                domain=route,
                title=title,
                content=content,
                date=date_entry,
            )
        )

    return entries
