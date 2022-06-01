from typing import Any, Final

import time


import celery
from celery.signals import worker_process_init
from celery.utils.dispatch.signal import Signal
from celery.utils.log import get_task_logger

import spacy
import selenium

from licenta_code.celery.common import CELERY_SEARCHER_TASK
from licenta_code.celery_searcher.celery_app import app
from licenta_code.celery_searcher.celery_worker import WorkerState

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

from licenta_code.scrapper.common import get_driver
from licenta_code.scrapper.model import Entry, SearchedNews


logger = get_task_logger(__name__)
worker_state: WorkerState

searching_soft_time_limit: Final = 10 * 300
searching_hard_time_limit: Final = 11 * 300
searching_lock_time_limit: Final = searching_hard_time_limit + 300

driver = get_driver()
nlp = spacy.load("ro_core_news_sm")

pos_tag = ["PROPN", "ADJ", "NOUN"]


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


def get_url(search):
    try:
        elem = search.find_element_by_css_selector("a")
        url = elem.get_attribute("href")
    except Exception:
        url = ""
    return url


def get_slug(search, url):
    while True:
        try:
            elem = search.find_element_by_css_selector("cite > span")
            slugs = elem.text
            if slugs[-3:] == "...":
                slugs = url.split("/")[-1]
            else:
                slugs = slugs.split(" ")[-1]
            break
        except selenium.common.exceptions.StaleElementReferenceException:
            continue
        except selenium.common.exceptions.NoSuchElementException:
            slugs = ""
            break
    return slugs


def get_meta(search):
    try:
        elem = search.find_element_by_css_selector('div[class^="VwiC3b"]')
        meta = elem.text

        if meta[-3:] == "...":
            meta = meta[:-3]
        if "—" in meta[:20]:
            pos = meta.find("—") + 2
            meta = meta[pos:]
    except selenium.common.exceptions.NoSuchElementException:
        meta = ""
    return meta


def accept_google_terms():
    driver.get("https://www.google.ro/")
    try:
        accept_button = WebDriverWait(driver, 3).until(
            expected_conditions.presence_of_element_located((By.ID, "L2AGLb"))
        )
        accept_button.click()
    except selenium.common.exceptions.TimeoutException:
        pass


def extract_keywords(text: str) -> list[str]:
    doc = nlp(text)
    return [key.lemma_ for key in doc.ents]


def extract_first_page_links(keywords: list[str]) -> list[dict[str, str]]:
    driver.get(
        "https://www.google.ro/search?q=" + "+".join([keyword for keyword in keywords])
    )
    time.sleep(3)
    try:
        searches = (
            WebDriverWait(driver, 10)
            .until(expected_conditions.presence_of_element_located((By.ID, "rso")))
            .find_elements_by_xpath("*")
        )
    except selenium.common.exceptions.NoSuchElementException:
        return []
    except selenium.common.exceptions.TimeoutException:
        return []

    searches_data = []
    if searches is not None:
        for search in searches:
            class_name = search.get_attribute("class")

            if class_name is None:
                continue
            if class_name not in ["g tF2Cxc", "hlcw0c"]:
                continue

            url = get_url(search)
            if (
                "facebook" in url
                or "twitter" in url
                or "youtube" in url
                or "linkedin" in url
                or "instagram" in url
            ):
                continue

            slug = get_slug(search, url)
            meta = get_meta(search)

            searches_data.append({"url": url, "slug": slug, "meta": meta})

    return searches_data


def search():
    global worker_state

    accept_google_terms()

    col = worker_state.mongodb_connect_to_collection()

    index: int = 0
    for entry in (
        col.find({"searched": 0, "title_keywords": {"$exists": False}})
        .limit(100)
        .sort("date", 1)
    ):
        index += 1
        if index == 100:
            break
        entry_obj = Entry.parse_obj(entry)
        entry_obj.title_keywords = extract_keywords(entry_obj.title)
        entry_obj.content_keywords = extract_keywords(entry_obj.content)

        try:
            alike_news = []
            if len(entry_obj.title_keywords) >= 1:
                links_to_search: list[str] = [
                    link
                    for link in extract_first_page_links(entry_obj.title_keywords)
                    if link != entry_obj.link
                ]
                alike_news = [SearchedNews(**link).dict() for link in links_to_search]

            if len(alike_news) == 0:
                raise Exception("No news found")
            col.update_one(
                {"_id": entry.get("_id")},
                {
                    "$set": {
                        "searched": 1,
                        "title_keywords": entry_obj.title_keywords,
                        "content_keywords": entry_obj.content_keywords,
                        "alike_news": alike_news,
                    }
                },
            )
        except Exception:
            col.update_one(
                {"_id": entry.get("_id")},
                {
                    "$set": {
                        "searched": -1,
                        "title_keywords": entry_obj.title_keywords,
                        "content_keywords": entry_obj.content_keywords,
                        "alike_news": alike_news,
                    }
                },
            )


@app.task(
    bind=True,
    name=CELERY_SEARCHER_TASK,
    time_limit=searching_hard_time_limit,
    soft_time_limit=searching_soft_time_limit,
)
def celery_fill_scrapper(
    self: celery.Task,
    **kwargs: Any,
) -> None:
    pre_str = "celery searcher"
    logger.info(pre_str)

    global worker_state

    lock_name = f"{CELERY_SEARCHER_TASK}_lock"
    have_lock = False
    lock = worker_state.redis_client.lock(
        name=lock_name, timeout=searching_lock_time_limit
    )
    try:
        have_lock = lock.acquire(blocking=False)
        if have_lock:
            try:
                search()
            except Exception as e:
                print(e)
        else:
            logger.info(f"{pre_str}: lock taken")
    finally:
        if have_lock:
            lock.release()
