from typing import Any
import json
import datetime

from celery import Celery
import kombu.serialization

from celery_beat.common import get_cfg


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
    broker=cfg.broker_url,
    autofinalize=True,
)
kombu.serialization.pickle_protocol = cfg.pickle_protocol
app.conf = app.config_from_object(cfg.dict(), force=True)

conf_json = json.dumps(dict(app.conf), indent=4, cls=Encoder)
print(f"app conf: {conf_json}")
