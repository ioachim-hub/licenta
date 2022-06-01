from typing import Any, Final
import re

import torch
from transformers import AutoTokenizer, AutoModel

import sklearn.metrics.pairwise

import celery
from celery.signals import worker_process_init
from celery.utils.dispatch.signal import Signal
from celery.utils.log import get_task_logger


from licenta_code.celery.common import CELERY_SIMILARITY_TASK
from licenta_code.celery_similarity.celery_app import app
from licenta_code.celery_similarity.celery_worker import WorkerState

from licenta_code.scrapper.model import Entry


logger = get_task_logger(__name__)
worker_state: WorkerState

similarity_soft_time_limit: Final = 10 * 600
similarity_hard_time_limit: Final = 11 * 600
similarity_lock_time_limit: Final = similarity_hard_time_limit + 600

tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
model = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")


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


def calculate_similarity(list_text: list[str]) -> list[float]:
    tokens: dict[str, Any] = {"input_ids": [], "attention_mask": []}

    for sentence in list_text:
        # encode each sentence and append to dictionary
        new_tokens = tokenizer.encode_plus(
            sentence,
            max_length=128,
            truncation=True,
            padding="max_length",
            return_tensors="pt",
        )
        tokens["input_ids"].append(new_tokens["input_ids"][0])
        tokens["attention_mask"].append(new_tokens["attention_mask"][0])

    # reformat list of tensors into single tensor
    tokens["input_ids"] = torch.stack(tokens["input_ids"])
    tokens["attention_mask"] = torch.stack(tokens["attention_mask"])

    outputs = model(**tokens)
    embeddings = outputs.last_hidden_state
    attention_mask = tokens["attention_mask"]
    mask = attention_mask.unsqueeze(-1).expand(embeddings.size()).float()

    masked_embeddings = embeddings * mask
    summed = torch.sum(masked_embeddings, 1)
    summed_mask = torch.clamp(mask.sum(1), min=1e-9)

    mean_pooled = summed / summed_mask

    mean_pooled = mean_pooled.detach().numpy()

    return sklearn.metrics.pairwise.cosine_similarity([mean_pooled[0]], mean_pooled[1:])


"""
regex:

    ^(?P<link>.*)$
    [int]
    /( /)

"""

space = re.compile(r" +")
numbers = re.compile(r"\[[1-9]+\]")
para = re.compile(r"\([1-9]+\)")
ghi = re.compile(r"'")
abos = re.compile(r'"')


def clean_text(text: str) -> str:
    text = numbers.sub(" ", text)
    text = ghi.sub(" ", text)
    text = abos.sub(" ", text)
    text = para.sub(" ", text)
    text = space.sub(" ", text).strip()
    return text


def similarity():
    global worker_state

    col = worker_state.mongodb_connect_to_collection()

    index: int = 0
    for entry in col.find({"searched": 2}).sort("date", -1).limit(100):
        index += 1
        if index == 100:
            break
        entry_obj = Entry.parse_obj(entry)
        logger.info(f"{entry_obj.site} - {entry_obj.title}")

        sentences_list_title: list[str] = [entry_obj.title]
        indexes_list_title: list[int] = []
        for index, alike_news in enumerate(entry_obj.alike_news):
            if alike_news is not None:
                sentences_list_title.append(clean_text(alike_news.title))
                indexes_list_title.append(index)

        sentences_list_content: list[str] = [entry_obj.content]
        indexes_list_content: list[int] = []
        for index, alike_news in enumerate(entry_obj.alike_news):
            if alike_news is not None:
                sentences_list_content.append(clean_text(alike_news.text))
                indexes_list_content.append(index)

        if len(sentences_list_title) == 0 and len(sentences_list_content) == 0:
            continue

        try:
            similarities_title = calculate_similarity(sentences_list_title)
            similarities_content = calculate_similarity(sentences_list_content)
        except Exception as e:
            logger.error(f"Error calculating similarity for entry {entry_obj.title}")
            logger.error(e)
            col.update_one(
                {"_id": entry.get("_id")},
                {"$set": {"searched": -3}},
            )
            continue

        for index, similarity_title, similarity_content in zip(
            indexes_list_title, similarities_title[0], similarities_content[0]
        ):
            entry_obj.alike_news[index].similarity_title = similarity_title
            entry_obj.alike_news[index].similarity_content = similarity_content
            if entry_obj.alike_news[index].similarity_title > 0.5:
                entry_obj.alike_news[index].has_similar_title = True
            else:
                entry_obj.alike_news[index].has_similar_title = False
            if entry_obj.alike_news[index].similarity_content > 0.5:
                entry_obj.alike_news[index].has_similar_content = True
            else:
                entry_obj.alike_news[index].has_similar_content = False

            col.update_one(
                {"_id": entry.get("_id")},
                {
                    "$set": {
                        f"alike_news.{index}.similarity_title": float(
                            entry_obj.alike_news[index].similarity_title
                        ),
                        f"alike_news.{index}.similarity_content": float(
                            entry_obj.alike_news[index].similarity_content
                        ),
                        f"alike_news.{index}.has_similar_title": float(
                            entry_obj.alike_news[index].has_similar_title
                        ),
                        f"alike_news.{index}.has_similar_content": float(
                            entry_obj.alike_news[index].has_similar_content
                        ),
                    }
                },
            )
        col.update_one(
            {"_id": entry.get("_id")},
            {"$set": {"searched": 3}},
        )


@app.task(
    bind=True,
    name=CELERY_SIMILARITY_TASK,
    time_limit=similarity_hard_time_limit,
    soft_time_limit=similarity_soft_time_limit,
)
def celery_fill_scrapper(
    self: celery.Task,
    **kwargs: Any,
) -> None:
    pre_str = "celery similarity"
    logger.info(pre_str)

    global worker_state

    lock_name = f"{CELERY_SIMILARITY_TASK}_lock"
    have_lock = False
    lock = worker_state.redis_client.lock(
        name=lock_name, timeout=similarity_lock_time_limit
    )
    try:
        have_lock = lock.acquire(blocking=False)
        if have_lock:
            try:
                similarity()
            except Exception as e:
                print(e)
        else:
            logger.info(f"{pre_str}: lock taken")
    finally:
        if have_lock:
            lock.release()
