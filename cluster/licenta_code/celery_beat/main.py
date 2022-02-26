from typing import Any
import logging

import celery

from licenta_code.celery.common import (
    CELERY_SCRAPP_QUEUE,
    CELERY_SCRAPP_TASK,
)

from licenta_code.celery_beat.celery_app import app, cfg

app.conf.update(
    beat_max_loop_interval=60,
)


@app.on_after_finalize.connect
def setup_periodic_tasks(
    sender: celery.Celery,
    **kwargs: Any,
) -> None:
    logging.info("populating scheduler...")
    for site in cfg.site:
        for route in site.routes:
            day_freq_sec = 300
            ts_freq_sec = 3600

            expires = int(ts_freq_sec * cfg.celery.expires_multiplier)
            req = celery.signature(
                CELERY_SCRAPP_TASK,
                kwargs=dict(url=site.url, route=route),
                queue=CELERY_SCRAPP_QUEUE,
                expires=expires,
                immutable=True,
            )
            sender.add_periodic_task(day_freq_sec, req)

    logging.info("done")
