from typing import Any
import json
import datetime

from celery import Celery
import kombu.serialization

from fakepred.celery_similarity.common import get_cfg

cfg = get_cfg()


class Encoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime.timedelta):
            return str(obj)
        elif isinstance(obj, set):
            return str(obj)
        else:
            return json.JSONEncoder.default(self, obj)


cfg = get_cfg()

app = Celery(
    "main",
    broker=cfg.celery.broker_url,
    include=["fakepred.celery_similarity.tasks"],
    autofinalize=True,
)
kombu.serialization.pickle_protocol = cfg.celery.pickle_protocol
app.conf = app.config_from_object(cfg.celery.dict(), force=True)

conf_json = json.dumps(dict(app.conf), indent=4, cls=Encoder)
print(f"app conf: {conf_json}")
