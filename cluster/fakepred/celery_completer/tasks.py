from typing import Any, Final

import dataclasses

import bs4
import requests_html

import celery
from celery.signals import worker_process_init
from celery.utils.dispatch.signal import Signal
from celery.utils.log import get_task_logger

from fakepred.celery.common import CELERY_COMPLETER_TASK
from fakepred.celery_completer.celery_app import app
from fakepred.celery_completer.celery_worker import WorkerState

from fakepred.scrapper.model import Entry


logger = get_task_logger(__name__)
worker_state: WorkerState

searching_soft_time_limit: Final = 10 * 300
searching_hard_time_limit: Final = 11 * 300
searching_lock_time_limit: Final = searching_hard_time_limit + 300


@dataclasses.dataclass
class NewsInfo:
    title: str
    content: str


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


"""
TODO: regex
\xa0
•
\u2022
\u25e6
\r\n\t
"""


def clean_text(text: str) -> str:
    text = text.replace("\n", " ")
    text = text.replace("\r", " ")
    text = text.replace("\t", " ")
    text = text.replace("\xa0", " ")
    text = text.replace("•", " ")
    text = text.replace("\u2022", " ")
    text = text.replace("\u25e6", " ")
    text = text.strip()
    return text


def extract_from_news(url: str) -> NewsInfo:
    empty_return = NewsInfo("", "")
    if url.split(".")[-1] in ["pdf", "doc", "docx", "xls", "xlsx", "txt"]:
        return empty_return

    if url.split(".")[-1] in ["jpg", "jpeg", "png"]:
        return empty_return

    if ".pdf" in url:
        return empty_return

    session = requests_html.HTMLSession()
    data = session.get(url, timeout=10)

    if "PDF" in data.text:
        return empty_return

    soup = bs4.BeautifulSoup(data.text)
    title: str = " ".join([p.text for p in soup.find_all("title")])
    title += " ".join([p.text for p in soup.find_all("h1")])
    title = clean_text(title)

    content: str = " ".join([p.text for p in soup.find_all("p")])
    content = clean_text(content)

    content = " ".join(
        [word for word in content.split(" ")[: min(len(content.split(" ")), 1000)]]
    )

    return NewsInfo(title=title, content=content)


def complete():
    global worker_state

    col = worker_state.mongodb_connect_to_collection()
    index: int = 0
    for entry in col.find({"searched": 1}).limit(100).sort("date", 1):
        index += 1
        if index == 100:
            break
        entry_obj = Entry.parse_obj(entry)

        for index, news in enumerate(entry_obj.alike_news):
            if news is None:
                continue

            try:
                extract = extract_from_news(news.url)
            except Exception as e:
                print(e)

            try:
                col.update_one(
                    {"_id": entry.get("_id")},
                    {
                        "$set": {
                            f"alike_news.{index}.title": extract.title,
                            f"alike_news.{index}.text": extract.content,
                        }
                    },
                )

            except Exception:
                col.update_one(
                    {"_id": entry.get("_id")},
                    {"$set": {"searched": -2}},
                )
        col.update_one(
            {"_id": entry.get("_id")},
            {"$set": {"searched": 2}},
        )


@app.task(
    bind=True,
    name=CELERY_COMPLETER_TASK,
    time_limit=searching_hard_time_limit,
    soft_time_limit=searching_soft_time_limit,
)
def celery_fill_scrapper(
    self: celery.Task,
    **kwargs: Any,
) -> None:
    pre_str = "celery completer"
    logger.info(pre_str)

    global worker_state

    lock_name = f"{CELERY_COMPLETER_TASK}_lock"
    have_lock = False
    lock = worker_state.redis_client.lock(
        name=lock_name, timeout=searching_lock_time_limit
    )
    try:
        have_lock = lock.acquire(blocking=False)
        if have_lock:
            try:
                complete()
            except Exception as e:
                print(e)
        else:
            logger.info(f"{pre_str}: lock taken")
    finally:
        if have_lock:
            lock.release()
