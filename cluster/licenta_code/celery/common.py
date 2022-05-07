from typing import Optional, Literal
import datetime

import pydantic

CELERY_SCRAPP_QUEUE = "scrapp"
CELERY_SEARCHER_QUEUE = "searcher"
CELERY_COMPLETER_QUEUE = "completer"

CELERY_RSS_TASK = "rss"
CELERY_FILL_TASK = "fill"
CELERY_SCRAPP_TASK = "scrapp"
CELERY_SEARCH_TASK = "search"
CELERY_SEARCHER_TASK = "searcher"
CELERY_COMPLETER_TASK = "completer"


class CeleryConfig(pydantic.BaseModel):
    expires_multiplier: float = 2.0

    broker_url: str

    # https://docs.python.org/3/library/pickle.html#data-stream-format
    # https://docs.celeryproject.org/projects/kombu/en/master/userguide/serialization.html#serializers
    pickle_protocol: int = 5

    # config params from https://docs.celeryproject.org/en/stable/userguide/configuration.html

    accept_content: list[str] = ["json", "pickle"]
    # Serializers: https://docs.celeryproject.org/en/stable/userguide/calling.html#calling-serializers
    task_serializer: str = "pickle"
    event_serializer: str = "pickle"

    # Compression: https://docs.celeryproject.org/en/stable/userguide/calling.html#compression
    # NOTE: there is even zstd
    task_compression: Optional[str] = None

    # By default we will keep the results of a task
    # https://docs.celeryproject.org/en/stable/userguide/tasks.html#ignore-results-you-don-t-want
    task_ignore_result: bool = False
    task_store_errors_even_if_ignored: bool = False
    task_track_started: bool = False

    # WARNING: does not seem to be honored ?
    task_default_delivery_mode: Literal["transient", "persistent"] = "transient"
    broker_connection_timeout: int = 30
    broker_pool_limit: int = 256

    worker_cancel_long_running_tasks_on_connection_loss: bool = True

    # example: rpc://
    result_backend: Optional[str] = None
    result_persistent: bool = False
    result_compression: Optional[str] = None
    result_serializer: str = "pickle"
    result_accept_content: list[str] = ["json", "pickle"]
    result_expires: datetime.timedelta = datetime.timedelta(minutes=10)
    result_extended: bool = False
