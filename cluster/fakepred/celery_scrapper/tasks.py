from typing import Any, Final
import pandas as pd

import celery
from celery.signals import worker_process_init
from celery.utils.dispatch.signal import Signal
from celery.utils.log import get_task_logger

import selenium

from requests_html import HTMLSession

from fakepred.celery.common import (
    CELERY_RSS_TASK,
    CELERY_SCRAPP_TASK,
    CELERY_SEARCH_TASK,
    CELERY_FILL_TASK,
    CELERY_SCRAPP_QUEUE,
)

from fakepred.celery_scrapper.celery_app import app
from fakepred.celery_scrapper.celery_worker import WorkerState

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

from fakepred.mongodb.common import MONGODB_SCRAPPED_COLLECTION_NAME
from fakepred.scrapper.model import Entry
from fakepred.scrapper.common import get_driver

from fakepred.scrapper.scrapper_logic import (
    scrapper_logic_tnr,
    scrapper_logic_digi,
    scrapper_logic_aktual,
    scrapper_logic_activenews,
    scrapper_logic_infoalert,
    scrapper_logic_caplimpede,
)
from fakepred.scrapper.search_logic import search_logic
from fakepred.scrapper.rss_logic import rss_logic
from fakepred.scrapper.fill_logic import fill_logic

from fakepred.scrapper.common import convert_date

logger = get_task_logger(__name__)
worker_state: WorkerState
scrapping_soft_time_limit: Final = 10 * 120
scrapping_hard_time_limit: Final = 11 * 120
scrapping_lock_time_limit: Final = scrapping_hard_time_limit + 60

searching_soft_time_limit: Final = 10 * 180
searching_hard_time_limit: Final = 11 * 180
searching_lock_time_limit: Final = searching_hard_time_limit + 180
driver = get_driver()


@worker_process_init.connect
def worker_process_init_fn(
    signal: Signal,
    **kwargs: Any,
) -> None:
    """
    Process level init callback.
    """
    global worker_state
    worker_state = WorkerState()


def find_last_page_tnr(url: str, route: str) -> int:
    logger.info("find last page on TNR")

    driver.get(url + route)
    number = WebDriverWait(driver, 3).until(
        expected_conditions.presence_of_all_elements_located(
            (By.XPATH, "/html/body/section/div/div[2]/div[1]/div[2]/div/a[2]")
        )
    )
    return int(number[0].accessible_name)


def find_last_page_digi(url: str, route: str) -> int:
    logger.info("find last page on digi")

    driver.get(f"{url + route}?p=9999")
    number = WebDriverWait(driver, 3).until(
        expected_conditions.presence_of_all_elements_located(
            (By.XPATH, "/html/body/main/section/div[3]/div/div[1]/nav/div/div[2]/a[5]")
        )
    )
    return int(number[0].accessible_name)


def find_last_page_aktual(url: str, route: str) -> int:
    logger.info("find last page on aktual")

    driver.get(f"{url + route}")
    number = WebDriverWait(driver, 3).until(
        expected_conditions.presence_of_all_elements_located(
            (By.XPATH, "//*[@id='main']/nav/ul/li[8]/a")
        )
    )
    return int(number[0].accessible_name.replace(".", ""))


def find_last_page_infoalert(url: str, route: str) -> int:
    logger.info("find last page on infoalert")

    driver.get(f"{url + route}")
    try:
        number = WebDriverWait(driver, 3).until(
            expected_conditions.presence_of_all_elements_located(
                (
                    By.CSS_SELECTOR,
                    "#td-outer-wrap > div > div.td-container.td-category-container > div > div > "
                    + "div.td-pb-span8.td-main-content > div > div.page-nav.td-pb-padding-side > span.pages",
                )
            )
        )
        return int(number[0].text.split(" ")[-1])
    except Exception:
        return 1


def find_last_page_caplimpede(url: str, route: str) -> int:
    logger.info("find last page on camlimpede")

    driver.get(f"{url + route}")
    try:
        number = WebDriverWait(driver, 3).until(
            expected_conditions.presence_of_all_elements_located(
                (
                    By.CSS_SELECTOR,
                    "#td-outer-wrap > div > div.td-container.td-category-container > div > div:nth-child(2) > "
                    + "div.td-pb-span8.td-main-content > div > div.page-nav.td-pb-padding-side > span.pages",
                )
            )
        )
        return int(number[0].text.split(" ")[-1].replace(".", ""))
    except Exception:
        return 1


def find_last_page_activenews(url: str, route: str) -> int:
    logger.info("find last page on activenews")

    for page in range(50, 0, -1):
        driver.get(f"{url + route}pagina-{page}")
        try:
            button = WebDriverWait(driver, 3).until(
                expected_conditions.presence_of_all_elements_located(
                    (
                        By.CSS_SELECTOR,
                        "#chrome > div.row.article-list > div > div:nth-child(1) > main > div.paginatie.cf > a",
                    )
                )
            )
        except selenium.common.exceptions.TimeoutException:
            continue
        if button is not None:
            return page + 1
    return 1


def get_dates_tnr(path: str, mid: int) -> list[pd.Timestamp]:
    logger.info("date dates tnr")

    driver.get(f"{path}/page/{mid}")
    articles = WebDriverWait(driver, 3).until(
        expected_conditions.presence_of_all_elements_located(
            (By.CSS_SELECTOR, 'article[class^="article-box"]')
        )
    )
    dates = []
    for idx in range(len(articles)):
        elems_dates = articles[idx].find_elements_by_class_name("date")
        new_dates = [
            pd.to_datetime(convert_date(el.text), format="%d %m %Y")
            for el in elems_dates
        ]
        dates.extend(new_dates)
    dates.sort()

    return dates


def get_dates_digi(path: str, mid: int) -> list[pd.Timestamp]:
    logger.info("get dates digi")

    session = HTMLSession()

    driver.get(f"{path}?p={mid}")
    articles = WebDriverWait(driver, 3).until(
        expected_conditions.presence_of_all_elements_located((By.TAG_NAME, "article"))
    )
    dates = []
    for idx in range(len(articles)):
        elems_dates = articles[idx].find_elements_by_css_selector("h2 > a")
        data = session.get(elems_dates[0].get_attribute("href"))
        date = pd.to_datetime(
            data.html.find(
                "#article-content > article > div > div.flex.flex-center > div"
                + " > div > div:nth-child(1) > div > div > span > time"
            )[0]
            .text.encode("utf-8")
            .decode(),
            format="%d.%m.%Y %H:%M",
        )
        dates.append(date)
    dates.sort()

    return dates


def get_dates_aktual(path: str, mid: int) -> list[pd.Timestamp]:
    logger.info("get dates aktual")

    session = HTMLSession()

    driver.get(f"{path}/page/{mid}")
    articles = WebDriverWait(driver, 3).until(
        expected_conditions.presence_of_all_elements_located((By.TAG_NAME, "article"))
    )
    dates = []
    for idx in range(len(articles)):
        try:
            elems_dates = articles[idx].find_elements_by_css_selector("h1 > a")
            data = session.get(elems_dates[0].get_attribute("href"))
            date = pd.to_datetime(
                data.html.find(
                    "div.art-info > p.byline.entry-meta.vcard > span > time"
                )[0].attrs["datetime"],
                format="%Y-%m-%d",
            )
            dates.append(date)
        except Exception:
            continue
    dates.sort()

    return dates


def get_dates_activenews(path: str, mid: int) -> list[pd.Timestamp]:
    logger.info("get dates activenews")

    session = HTMLSession()

    driver.get(f"{path}/pagina-{mid}")
    articles = WebDriverWait(driver, 3).until(
        expected_conditions.presence_of_all_elements_located((By.TAG_NAME, "article"))
    )
    dates = []
    for idx in range(len(articles)):
        try:
            elems_dates = articles[idx].find_elements_by_css_selector("h2 > a")
            data = session.get(elems_dates[0].get_attribute("href"))
            date = pd.to_datetime(
                convert_date(
                    data.html.find(
                        "div.row > div > div > div.article-meta > span.article-date"
                    )[0].text.split(", ")[1]
                ),
                format="%d %m %Y",
            )
            dates.append(date)
        except Exception:
            continue
    dates.sort()

    return dates


def get_dates_infoalert(path: str, mid: int) -> list[pd.Timestamp]:
    logger.info("get dates infoalert")

    driver.get(f"{path}/page/{mid}")
    articles = WebDriverWait(driver, 3).until(
        expected_conditions.presence_of_all_elements_located(
            (
                By.CSS_SELECTOR,
                "#td-outer-wrap > div > div.td-container.td-category-container > div > div > "
                + "div.td-pb-span8.td-main-content > div > div",
            )
        )
    )
    dates = []
    for idx in range(len(articles)):
        try:
            date = pd.to_datetime(
                convert_date(
                    articles[idx]
                    .find_elements_by_css_selector(
                        "div.item-details > div.meta-info > span.td-post-date > time"
                    )[0]
                    .text
                ),
                format="%d %m %Y",
            )
            dates.append(date)
        except Exception:
            continue
    dates.sort()

    return dates


def get_dates_caplimpede(path: str, mid: int) -> list[pd.Timestamp]:
    logger.info("get dates caplimpede")

    driver.get(f"{path}/page/{mid}")
    articles = WebDriverWait(driver, 3).until(
        expected_conditions.presence_of_all_elements_located(
            (
                By.CSS_SELECTOR,
                "#td-outer-wrap > div > div.td-container.td-category-container > div > "
                + "div:nth-child(2) > div.td-pb-span8.td-main-content > div > div",
            )
        )
    )
    dates = []
    for idx in range(len(articles)):
        try:
            date = pd.to_datetime(
                convert_date(
                    articles[idx].find_elements_by_css_selector("time")[0].text
                ),
                format="%d %m %Y",
            )
            dates.append(date)
        except Exception:
            continue
    dates.sort()

    return dates


# https://www.geeksforgeeks.org/python-program-for-binary-search/
# this code is modeled to serve the scope
def binary_search(low: int, high: int, date: pd.Timestamp, path: str) -> int:
    if high >= low:
        mid = (high + low) // 2

        dates: list[pd.Timestamp] = []
        if "https://www.timesnewroman.ro/" in path:
            dates = get_dates_tnr(path=path, mid=mid)
        elif "https://www.digi24.ro/" in path:
            dates = get_dates_digi(path=path, mid=mid)
        elif "https://www.aktual24.ro/" in path:
            dates = get_dates_aktual(path=path, mid=mid)
        elif "https://www.activenews.ro/" in path:
            dates = get_dates_activenews(path=path, mid=mid)
        elif "https://infoalert.ro/" in path:
            dates = get_dates_infoalert(path=path, mid=mid)
        elif "https://caplimpede.ro/" in path:
            dates = get_dates_caplimpede(path=path, mid=mid)

        if dates[0] <= date and dates[-1] >= date:
            return mid
        elif dates[0] < date:
            return binary_search(low, mid - 1, date, path)
        else:
            return binary_search(mid + 1, high, date, path)
    else:
        return -1


def check_first_page_tnr(url: str, route: str, date_: pd.Timestamp) -> bool:
    logger.info("check first page on tnr")

    driver.get(f"{url + route}/page/1")
    articles = WebDriverWait(driver, 3).until(
        expected_conditions.presence_of_all_elements_located(
            (By.CSS_SELECTOR, 'article[class^="article-box"]')
        )
    )
    dates = []
    for idx in range(len(articles)):
        elems_dates = articles[idx].find_elements_by_class_name("date")
        new_dates = [
            pd.to_datetime(convert_date(el.text), format="%d %m %Y")
            for el in elems_dates
        ]
        dates.extend(new_dates)
    dates.sort()

    if dates[0] <= date_ and dates[-1] >= date_:
        return False

    return True


def check_first_page_digi(url: str, route: str, date_: pd.Timestamp) -> bool:
    logger.info("check first page on digi")

    session = HTMLSession()

    driver.get(f"{url + route}?p=1")
    articles = WebDriverWait(driver, 3).until(
        expected_conditions.presence_of_all_elements_located((By.TAG_NAME, "article"))
    )
    dates = []
    for idx in range(len(articles)):
        elems_dates = articles[idx].find_elements_by_css_selector("h2 > a")
        data = session.get(elems_dates[0].get_attribute("href"))
        date = pd.to_datetime(
            data.html.find(
                "#article-content > article > div > div.flex.flex-center > div"
                + " > div > div:nth-child(1) > div > div > span > time"
            )[0]
            .text.encode("utf-8")
            .decode(),
            format="%d.%m.%Y %H:%M",
        )
        dates.append(date)
    dates.sort()

    if dates[0] <= date_ and dates[-1] >= date_:
        return False

    return True


def check_first_page_aktual(url: str, route: str, date_: pd.Timestamp) -> bool:
    logger.info("check first page on aktual")

    session = HTMLSession()

    driver.get(f"{url + route}/page/1")
    articles = WebDriverWait(driver, 3).until(
        expected_conditions.presence_of_all_elements_located((By.TAG_NAME, "article"))
    )
    dates = []
    for idx in range(len(articles)):
        try:
            elems_dates = articles[idx].find_elements_by_css_selector("h1 > a")
            data = session.get(elems_dates[0].get_attribute("href"))
            date = pd.to_datetime(
                data.html.find(
                    "div.art-info > p.byline.entry-meta.vcard > span > time"
                )[0].attrs["datetime"],
                format="%Y-%m-%d",
            )
            dates.append(date)
        except Exception:
            continue
    dates.sort()

    if dates[0] <= date_ and dates[-1] >= date_:
        return False

    return True


def check_first_page_activenews(url: str, route: str, date_: pd.Timestamp) -> bool:
    logger.info("check first page on activenews")

    session = HTMLSession()

    driver.get(f"{url + route}pagina-1")
    articles = WebDriverWait(driver, 3).until(
        expected_conditions.presence_of_all_elements_located((By.TAG_NAME, "article"))
    )
    dates = []
    for idx in range(len(articles)):
        try:
            elems_dates = articles[idx].find_elements_by_css_selector("h2 > a")
            data = session.get(elems_dates[0].get_attribute("href"))
            date = pd.to_datetime(
                convert_date(
                    data.html.find(
                        "div.row > div > div > div.article-meta > span.article-date"
                    )[0].text.split(", ")[1]
                ),
                format="%d %m %Y",
            )
            dates.append(date)
        except Exception:
            continue
    dates.sort()

    if dates[0] <= date_ and dates[-1] >= date_:
        return False

    return True


def check_first_page_infoalert(url: str, route: str, date_: pd.Timestamp) -> bool:
    logger.info("check first page on infoalert")

    driver.get(f"{url + route}page/1/")
    articles = WebDriverWait(driver, 3).until(
        expected_conditions.presence_of_all_elements_located(
            (
                By.CSS_SELECTOR,
                "#td-outer-wrap > div > div.td-container.td-category-container > div > "
                + "div > div.td-pb-span8.td-main-content > div",
            )
        )
    )
    dates = []
    for idx in range(len(articles)):
        try:
            date = pd.to_datetime(
                convert_date(
                    articles[idx].find_elements_by_css_selector("time")[0].text
                ),
                format="%d %m %Y",
            )
            dates.append(date)
        except Exception:
            continue
    dates.sort()

    if dates[0] <= date_ and dates[-1] >= date_:
        return False

    return True


def check_first_page_caplimpede(url: str, route: str, date_: pd.Timestamp) -> bool:
    logger.info("check first page on caplimpede")

    driver.get(f"{url + route}page/1/")
    articles = WebDriverWait(driver, 3).until(
        expected_conditions.presence_of_all_elements_located(
            (
                By.CSS_SELECTOR,
                "#td-outer-wrap > div > div.td-container.td-category-container > div > "
                + "div:nth-child(2) > div.td-pb-span8.td-main-content > div > div",
            )
        )
    )
    dates = []
    for idx in range(len(articles)):
        try:
            date = pd.to_datetime(
                convert_date(
                    articles[idx].find_elements_by_css_selector("time")[0].text
                ),
                format="%d %m %Y",
            )
            dates.append(date)
        except Exception:
            continue
    dates.sort()

    if dates[0] <= date_ and dates[-1] >= date_:
        return False

    return True


def find_page_by_date(url: str, route: str, date: pd.Timestamp, last_page: int) -> int:
    logger.info("find page by date")

    page = 1
    if url == "https://www.timesnewroman.ro/":
        if check_first_page_tnr(url=url, route=route, date_=date):
            page = binary_search(1, last_page, date, url + route)
    elif url == "https://www.digi24.ro/":
        if check_first_page_digi(url=url, route=route, date_=date):
            page = binary_search(1, last_page, date, url + route)
    elif url == "https://www.aktual24.ro/":
        if check_first_page_aktual(url=url, route=route, date_=date):
            page = binary_search(1, last_page, date, url + route)
    elif url == "https://www.activenews.ro/":
        if check_first_page_activenews(url=url, route=route, date_=date):
            page = binary_search(1, last_page, date, url + route)
    elif url == "https://infoalert.ro/":
        if check_first_page_infoalert(url=url, route=route, date_=date):
            page = binary_search(1, last_page, date, url + route)
    elif url == "https://caplimpede.ro/":
        if check_first_page_caplimpede(url=url, route=route, date_=date):
            page = binary_search(1, last_page, date, url + route)
    return page


def find_start_page(url: str, route: str) -> int:
    logger.info("find start page")

    last_page: int
    if url == "https://www.timesnewroman.ro/":
        last_page = find_last_page_tnr(url, route)
    elif url == "https://www.digi24.ro/":
        last_page = find_last_page_digi(url, route)
    elif url == "https://www.aktual24.ro/":
        last_page = find_last_page_aktual(url, route)
    elif url == "https://www.activenews.ro/":
        last_page = find_last_page_activenews(url, route)
    elif url == "https://infoalert.ro/":
        last_page = find_last_page_infoalert(url, route)
    elif url == "https://caplimpede.ro/":
        last_page = find_last_page_caplimpede(url, route)

    entry: Entry = Entry()

    collection = worker_state.mongodb_db[MONGODB_SCRAPPED_COLLECTION_NAME]
    for e in collection.find({"site": url, "domain": route}).sort("date", -1):
        entry = Entry.parse_obj(e)
        break
    if entry.site == "":
        return last_page
    else:
        return find_page_by_date(url, route, entry.date, last_page)


def scrapper(url: str, route: str) -> None:
    logger.info("start scrapping")

    start_page = find_start_page(url, route)
    if start_page == -1:
        pass
    entry: Entry = Entry()
    collection = worker_state.mongodb_db[MONGODB_SCRAPPED_COLLECTION_NAME]
    for e in collection.find({"site": url, "domain": route}).sort("date", -1):
        entry = Entry.parse_obj(e)
        break
    for page in range(start_page, 0, -1):
        logger.info(f"scrapping from page: {page}")

        entries = []
        if url == "https://www.timesnewroman.ro/":
            entries = scrapper_logic_tnr(url, route, page, entry.date)
        elif url == "https://www.digi24.ro/":
            entries = scrapper_logic_digi(url, route, page, entry.date)
        elif url == "https://www.aktual24.ro/":
            entries = scrapper_logic_aktual(url, route, page, entry.date)
        elif url == "https://www.activenews.ro/":
            entries = scrapper_logic_activenews(url, route, page, entry.date)
        elif url == "https://infoalert.ro/":
            entries = scrapper_logic_infoalert(url, route, page, entry.date)
        elif url == "https://caplimpede.ro/":
            entries = scrapper_logic_caplimpede(url, route, page, entry.date)
        if entries == []:
            continue
        collection.insert_many([entry.dict() for entry in entries])


def search(url: str) -> None:
    logger.info("start searching")

    collection = worker_state.mongodb_db[MONGODB_SCRAPPED_COLLECTION_NAME]

    fil = {"domain": "", "title": "", "content": ""}
    driver.get(f"{url}")
    while True:
        entries_db: list[Entry] = []

        for e in collection.find(fil):
            entries_db.append(Entry.parse_obj(e))

        entries = search_logic(url=url, existing_entries=entries_db, driver=driver)
        if len(entries) != 0:
            collection.insert_many([entry.dict() for entry in entries])


def rss(url: str) -> None:
    logger.info("start rss")

    collection = worker_state.mongodb_db[MONGODB_SCRAPPED_COLLECTION_NAME]

    entries_db: list[Entry] = []

    for e in collection.find({"site": url}):
        entries_db.append(Entry.parse_obj(e))

    entries = rss_logic(url=url, existing_entries=entries_db)
    if len(entries) != 0:
        collection.insert_many([entry.dict() for entry in entries])

    req = celery.signature(
        CELERY_FILL_TASK,
        kwargs=dict(url=url),
        queue=CELERY_SCRAPP_QUEUE,
        immutable=True,
    )
    req.apply_async()


def fill(url: str) -> None:
    logger.info("start fill")

    collection = worker_state.mongodb_db[MONGODB_SCRAPPED_COLLECTION_NAME]

    entries_db: list[Entry] = []
    fil = {"domain": "", "title": "", "content": ""}
    for e in collection.find(fil):
        entries_db.append(Entry.parse_obj(e))

    entries = fill_logic(existing_entries=entries_db)
    if len(entries) != 0:
        for entry in entries:
            collection.update_one(
                filter={"link": entry.link},
                update={
                    "$set": {
                        "title": entry.title,
                        "content": entry.content,
                    },
                },
            )


@app.task(
    bind=True,
    name=CELERY_SCRAPP_TASK,
    time_limit=scrapping_hard_time_limit,
    soft_time_limit=scrapping_soft_time_limit,
)
def celery_scrapper(
    self: celery.Task,
    url: str,
    route: str,
    **kwargs: Any,
) -> None:
    pre_str = f"celery scrapper (url, route): ({url}, {route})"
    logger.info(pre_str)

    global worker_state

    lock_name = url + route
    have_lock = False
    lock = worker_state.redis_client.lock(
        name=lock_name, timeout=scrapping_lock_time_limit
    )
    try:
        have_lock = lock.acquire(blocking=False)
        if have_lock:
            scrapper(url=url, route=route)
        else:
            logger.info(f"{pre_str}: lock taken")
    finally:
        if have_lock:
            lock.release()


@app.task(
    bind=True,
    name=CELERY_SEARCH_TASK,
    time_limit=searching_hard_time_limit,
    soft_time_limit=searching_soft_time_limit,
)
def celery_link_searcher_scrapper(
    self: celery.Task,
    url: str,
    **kwargs: Any,
) -> None:
    pre_str = f"celery search (url): ({url})"
    logger.info(pre_str)

    global worker_state

    lock_name = url
    have_lock = False
    lock = worker_state.redis_client.lock(
        name=lock_name, timeout=scrapping_lock_time_limit
    )
    try:
        have_lock = lock.acquire(blocking=False)
        if have_lock:
            try:
                search(url=url)
            except Exception as e:
                print(e)
        else:
            logger.info(f"{pre_str}: lock taken")
    finally:
        if have_lock:
            lock.release()


@app.task(
    bind=True,
    name=CELERY_RSS_TASK,
    time_limit=searching_hard_time_limit,
    soft_time_limit=searching_soft_time_limit,
)
def celery_link_rss_scrapper(
    self: celery.Task,
    url: str,
    **kwargs: Any,
) -> None:
    pre_str = f"celery rss (url): ({url})"
    logger.info(pre_str)

    global worker_state

    lock_name = url
    have_lock = False
    lock = worker_state.redis_client.lock(
        name=lock_name, timeout=scrapping_lock_time_limit
    )
    try:
        have_lock = lock.acquire(blocking=False)
        if have_lock:
            try:
                rss(url=url)
            except Exception as e:
                print(e)
        else:
            logger.info(f"{pre_str}: lock taken")
    finally:
        if have_lock:
            lock.release()


@app.task(
    bind=True,
    name=CELERY_FILL_TASK,
    time_limit=searching_hard_time_limit,
    soft_time_limit=searching_soft_time_limit,
)
def celery_fill_scrapper(
    self: celery.Task,
    url: str,
    **kwargs: Any,
) -> None:
    pre_str = f"celery fill (url): ({url})"
    logger.info(pre_str)

    global worker_state

    lock_name = url
    have_lock = False
    lock = worker_state.redis_client.lock(
        name=lock_name, timeout=scrapping_lock_time_limit
    )
    try:
        have_lock = lock.acquire(blocking=False)
        if have_lock:
            try:
                fill(url=url)
            except Exception as e:
                print(e)
        else:
            logger.info(f"{pre_str}: lock taken")
    finally:
        if have_lock:
            lock.release()
