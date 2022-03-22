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


def scrapper_logic_tnr(
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
        if date_entry <= date_date:
            continue
        entries.append(
            Entry(
                site=url,
                domain=route,
                title=title,
                link=link,
                content=content,
                date=date_entry,
            )
        )

    return entries


def scrapper_logic_digi(
    url: str, route: str, page: int, date_date: pd.Timestamp
) -> list[Entry]:
    entries: list[Entry] = []
    print(f"scrapping from: {url}{route}?p={page})")

    driver.get(f"{url}{route}?p={page}")

    articles = WebDriverWait(driver, 3).until(
        expected_conditions.presence_of_all_elements_located((By.TAG_NAME, "article"))
    )

    links = []

    for idx in range(len(articles)):
        link = (
            articles[idx]
            .find_elements_by_css_selector("h2 > a")[0]
            .get_attribute("href")
        )
        links.append(link)

    session = HTMLSession()
    for link in links:
        data = session.get(link)
        date = pd.to_datetime(
            data.html.find(
                "#article-content > article > div > div.flex.flex-center > div"
                + " > div > div:nth-child(1) > div > div > span > time"
            )[0]
            .text.encode("utf-8")
            .decode(),
            format="%d.%m.%Y %H:%M",
        )
        title = data.html.find("h1")[0].text.encode("utf-8").decode()
        content = ""
        for paragraph in data.html.find(
            "#article-content > article > div > div.flex.flex-end.flex-center-md.flex-stretch >"
            + " div.col-8.col-md-9.col-sm-12 > div > div > div.entry.data-app-meta.data-app-meta-article > p"
        ):
            if "class" in paragraph.attrs:
                continue
            content += paragraph.text.encode("utf-8").decode()
        date_entry = pd.to_datetime(date)
        if date_entry <= date_date:
            continue
        entries.append(
            Entry(
                site=url,
                domain=route,
                title=title,
                link=link,
                content=content,
                date=date_entry,
            )
        )

    return entries


def scrapper_logic_aktual(
    url: str, route: str, page: int, date_date: pd.Timestamp
) -> list[Entry]:
    entries: list[Entry] = []
    print(f"scrapping from: {url}{route}page/{page}")

    driver.get(f"{url}{route}page/{page}")

    articles = WebDriverWait(driver, 3).until(
        expected_conditions.presence_of_all_elements_located((By.TAG_NAME, "article"))
    )

    links = []

    for idx in range(len(articles)):
        try:
            link = (
                articles[idx]
                .find_elements_by_css_selector("h1 > a")[0]
                .get_attribute("href")
            )
        except Exception:
            continue
        links.append(link)

    session = HTMLSession()
    for link in links:
        data = session.get(link)
        try:
            date = pd.to_datetime(
                data.html.find(
                    "div.art-info > p.byline.entry-meta.vcard > span > time"
                )[0].attrs["datetime"],
                format="%Y-%m-%d",
            )
            title = data.html.find("h1")[0].text.encode("utf-8").decode()
            content = ""
            for paragraph in data.html.find("div.single__content > p"):
                if "class" in paragraph.attrs:
                    continue
                content += paragraph.text.encode("utf-8").decode()
            date_entry = pd.to_datetime(date)
            if date_entry <= date_date:
                continue
            entries.append(
                Entry(
                    site=url,
                    domain=route,
                    title=title,
                    link=link,
                    content=content,
                    date=date_entry,
                )
            )
        except Exception:
            continue

    return entries


def scrapper_logic_activenews(
    url: str, route: str, page: int, date_date: pd.Timestamp
) -> list[Entry]:
    entries: list[Entry] = []
    print(f"scrapping from: {url}{route}pagina-{page}")

    driver.get(f"{url}{route}pagina-{page}")

    articles = WebDriverWait(driver, 3).until(
        expected_conditions.presence_of_all_elements_located((By.TAG_NAME, "article"))
    )

    links = []

    for idx in range(len(articles)):
        try:
            link = (
                articles[idx]
                .find_elements_by_css_selector("a")[0]
                .get_attribute("href")
            )
        except Exception:
            continue
        links.append(link)

    session = HTMLSession()
    for link in links:
        data = session.get(link)
        try:
            date = pd.to_datetime(
                convert_date(
                    data.html.find(
                        "div.row > div > div > div.article-meta > span.article-date"
                    )[0].text.split(", ")[1]
                ),
                format="%d %m %Y",
            )
            title = data.html.find("h1")[1].text.encode("utf-8").decode()
            content = ""
            for paragraph in data.html.find(
                "div.row > div > div > article > div.article-text > div.article-read > p"
            ):
                if "class" in paragraph.attrs:
                    continue
                content += paragraph.text.encode("utf-8").decode()
            date_entry = pd.to_datetime(date)
            if date_entry <= date_date:
                continue
            entries.append(
                Entry(
                    site=url,
                    domain=route,
                    title=title,
                    link=link,
                    content=content,
                    date=date_entry,
                )
            )
        except Exception:
            continue

    return entries


def scrapper_logic_infoalert(
    url: str, route: str, page: int, date_date: pd.Timestamp
) -> list[Entry]:
    entries: list[Entry] = []
    print(f"scrapping from: {url}{route}page/{page}")

    driver.get(f"{url}{route}page/{page}")

    articles = WebDriverWait(driver, 3).until(
        expected_conditions.presence_of_all_elements_located(
            (
                By.CSS_SELECTOR,
                "#td-outer-wrap > div > div.td-container.td-category-container > div > div >"
                + " div.td-pb-span8.td-main-content > div > div",
            )
        )
    )

    links = []

    for idx in range(len(articles)):
        try:
            link = (
                articles[idx]
                .find_elements_by_css_selector("a")[0]
                .get_attribute("href")
            )
        except Exception:
            continue
        links.append(link)

    session = HTMLSession()
    for link in links:
        data = session.get(link)
        try:
            date = pd.to_datetime(
                convert_date(
                    data.html.find(
                        "div.item-details > div.meta-info > span.td-post-date > time"
                    )[0].text
                ),
                format="%d %m %Y",
            )
            title = data.html.find("h1")[0].text.encode("utf-8").decode()
            content = ""
            for paragraph in data.html.find(
                "div.td-post-content.td-pb-padding-side > p"
            ):
                if "class" in paragraph.attrs:
                    continue
                content += paragraph.text.encode("utf-8").decode()
            date_entry = pd.to_datetime(date)
            if date_entry <= date_date:
                continue
            entries.append(
                Entry(
                    site=url,
                    domain=route,
                    title=title,
                    link=link,
                    content=content,
                    date=date_entry,
                )
            )
        except Exception:
            continue

    return entries


def scrapper_logic_caplimpede(
    url: str, route: str, page: int, date_date: pd.Timestamp
) -> list[Entry]:
    entries: list[Entry] = []
    print(f"scrapping from: {url}{route}page/{page}")

    driver.get(f"{url}{route}page/{page}")

    articles = WebDriverWait(driver, 3).until(
        expected_conditions.presence_of_all_elements_located(
            (
                By.CSS_SELECTOR,
                "#td-outer-wrap > div > div.td-container.td-category-container > div > "
                + "div:nth-child(2) > div.td-pb-span8.td-main-content > div > div",
            )
        )
    )

    links = []

    for idx in range(len(articles)):
        try:
            link = (
                articles[idx]
                .find_elements_by_css_selector("a")[0]
                .get_attribute("href")
            )
        except Exception:
            continue
        links.append(link)

    session = HTMLSession()
    for link in links:
        data = session.get(link)
        try:
            date = pd.to_datetime(
                convert_date(
                    data.html.find(
                        "div.td-post-header.td-pb-padding-side > header > div > span > time"
                    )[0].text
                ),
                format="%d %m %Y",
            )
            title = data.html.find("h1")[0].text.encode("utf-8").decode()
            content = ""
            for paragraph in data.html.find(
                "div.td-post-content.td-pb-padding-side > p"
            ):
                if "class" in paragraph.attrs:
                    continue
                content += paragraph.text.encode("utf-8").decode()
            date_entry = pd.to_datetime(date)
            if date_entry <= date_date:
                continue
            entries.append(
                Entry(
                    site=url,
                    domain=route,
                    title=title,
                    link=link,
                    content=content,
                    date=date_entry,
                )
            )
        except Exception:
            continue

    return entries
