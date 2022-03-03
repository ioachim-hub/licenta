from typing import Any, Final
import pandas as pd

import celery
from celery.signals import worker_process_init
from celery.utils.dispatch.signal import Signal
from celery.utils.log import get_task_logger

from licenta_code.celery.common import (
    CELERY_RSS_TASK,
    CELERY_SCRAPP_TASK,
    CELERY_SEARCH_TASK,
    CELERY_FILL_TASK,
    CELERY_SCRAPP_QUEUE,
)

from licenta_code.celery_scrapper.celery_app import app
from licenta_code.celery_scrapper.celery_worker import WorkerState

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

from licenta_code.mongodb.common import MONGODB_SCRAPPED_COLLECTION_NAME
from licenta_code.scrapper.model import Entry
from licenta_code.scrapper.common import get_driver

from licenta_code.scrapper.scrapper_logic import scrapper_logic
from licenta_code.scrapper.search_logic import search_logic
from licenta_code.scrapper.rss_logic import rss_logic
from licenta_code.scrapper.fill_logic import fill_logic

from licenta_code.scrapper.common import convert_date

logger = get_task_logger(__name__)
worker_state: WorkerState
scrapping_soft_time_limit: Final = 10 * 60
scrapping_hard_time_limit: Final = 11 * 60
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


def find_last_page(url: str, route: str) -> int:
    driver.get(url + route)
    number = WebDriverWait(driver, 3).until(
        expected_conditions.presence_of_all_elements_located(
            (By.XPATH, "/html/body/section/div/div[2]/div[1]/div[2]/div/a[2]")
        )
    )
    return int(number[0].accessible_name)


# https://www.geeksforgeeks.org/python-program-for-binary-search/
# this code is modeled to serve the scope
def binary_search(low: int, high: int, date: pd.Timestamp, path: str) -> int:
    if high >= low:
        mid = (high + low) // 2

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

        if dates[0] <= date and dates[-1] >= date:
            return mid
        elif dates[0] < date:
            return binary_search(low, mid - 1, date, path)
        else:
            return binary_search(mid + 1, high, date, path)
    else:
        return -1


def check_first_page(url: str, route: str, date: pd.Timestamp) -> bool:
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

    if dates[0] <= date and dates[-1] >= date:
        return False

    return True


def find_page_by_date(url: str, route: str, date: pd.Timestamp) -> int:
    page = 1
    if check_first_page(url=url, route=route, date=date):
        last_page = find_last_page(url, route)
        page = binary_search(1, last_page, date, url + route)
    return page


def find_start_page(url: str, route: str) -> int:
    last_page = find_last_page(url, route)
    entry: Entry
    collection = worker_state.mongodb_db[MONGODB_SCRAPPED_COLLECTION_NAME]
    for e in collection.find({"site": url, "domain": route}).sort("date", -1):
        entry = Entry.parse_obj(e)
        break
    if entry is None:
        return last_page
    else:
        return find_page_by_date(url, route, entry.date)


def scrapper(url: str, route: str) -> None:
    start_page = find_start_page(url, route)
    if start_page == -1:
        pass
    entry: Entry
    collection = worker_state.mongodb_db[MONGODB_SCRAPPED_COLLECTION_NAME]
    for e in collection.find({"site": url, "domain": route}).sort("date", -1):
        entry = Entry.parse_obj(e)
        break
    for page in range(start_page, 0, -1):
        entries = scrapper_logic(url, route, page, entry.date)
        if entries == []:
            continue
        collection.insert_many([entry.dict() for entry in entries])


def search(url: str) -> None:
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
            search(url=url)
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
            rss(url=url)
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
        # if have_lock:
        fill(url=url)
        # else:
        logger.info(f"{pre_str}: lock taken")
    finally:
        if have_lock:
            lock.release()
