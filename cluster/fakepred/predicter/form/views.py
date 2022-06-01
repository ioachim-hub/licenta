from typing import Optional

import json
import requests  # type: ignore
import datetime
import dataclasses

import django
import django.shortcuts


from form.form import ArticleForm, MONGODB_NEWS_COLLECTION_NAME, MongoForm
from utils import dbHandler
from model.common import (
    extract_from_news,
    NewsInfo,
)
from cleaner.model import Cleaner

cleaner = Cleaner()


db = dbHandler(
    db_name="news",
    host="mongodb",
    port=27017,
    username="root",
    password="ikkgIzSjBW",
)


@dataclasses.dataclass
class Response:
    news_list: list[MongoForm] = dataclasses.field(default_factory=list)
    form: Optional[NewsInfo] = None


def index(request: django.http.HttpRequest):
    collection = db.get_db_handle()[MONGODB_NEWS_COLLECTION_NAME]
    news = collection.find().limit(25).sort("uuid", -1)
    news_list = []
    for new in news:
        news_list.append(MongoForm.parse_obj(new))
    response: Response = Response(news_list=news_list)
    return django.shortcuts.render(
        request, "form/index.html", context={"result": response}
    )


@django.views.decorators.csrf.csrf_protect
def upload(request: django.http.HttpRequest):
    collection = db.get_db_handle()[MONGODB_NEWS_COLLECTION_NAME]
    news = collection.find().limit(25).sort("uuid", -1)
    news_list = []
    for new in news:
        news_list.append(MongoForm.parse_obj(new))
    print(news_list)
    form = ArticleForm()
    response: Response = Response(news_list=news_list)

    uuid = 1
    if len(news_list) > 0:
        uuid = news_list[0].uuid + 1
    # if this is a POST request we need to process the form data
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        form = ArticleForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            if (
                form.cleaned_data.get("title") != ""
                and form.cleaned_data.get("content") != ""
            ):
                link = form.cleaned_data.get("link")

                outputs_title: float = 0.5
                outputs_content: float = 0.5

                title = form.cleaned_data.get("title")
                if title is not None:
                    title = cleaner.map_dataframe(title, 0, 0.2, 0.2)[0]

                content = form.cleaned_data.get("content")
                if content is not None:
                    content = cleaner.map_dataframe(content, 0, 0.2, 0.2)[0]

                try:
                    outputs = requests.post(
                        "http://restapi-content-predicter:80/predict",
                        data=json.dumps({"content": content}),
                    ).json()
                    outputs_content = outputs["score"]
                except Exception:
                    outputs_content = 0.5

                try:
                    outputs = requests.post(
                        "http://restapi-title-predicter:80/predict",
                        data=json.dumps({"content": title}),
                    ).json()
                    outputs_title = outputs["score"]
                except Exception:
                    outputs_title = 0.5

                label = 80 * outputs_content / 100 + 20 * outputs_title / 100
                entry = MongoForm(
                    uuid=uuid,
                    title=form.cleaned_data.get("title"),
                    content=form.cleaned_data.get("content"),
                    title_score=outputs_title,
                    content_score=outputs_content,
                    label=label,
                    link=link,
                    date=datetime.datetime.now(),
                )

                try:
                    collection.insert_one(entry.dict())
                except Exception:
                    return django.http.HttpResponseRedirect("error")

                return django.shortcuts.render(
                    request, "form/news.html", context={"result": entry}
                )
            else:
                try:
                    news_info: NewsInfo = extract_from_news(
                        form.cleaned_data.get("link")
                    )
                except Exception:
                    return django.http.HttpResponseRedirect("error")
                response.form = news_info
                return django.shortcuts.render(
                    request,
                    "form/index.html",
                    context={"form": form, "result": response},
                )

    return django.shortcuts.render(
        request, "form/index.html", context={"form": form, "result": response}
    )


def error(request: django.http.HttpRequest):
    return django.http.HttpResponseBadRequest("Server error")


def news(request: django.http.HttpRequest):
    db_handle = db.get_db_handle()

    collection = db_handle[MONGODB_NEWS_COLLECTION_NAME]

    news = collection.find().limit(25)
    news_list = []
    for new in news:
        news_list.append(MongoForm.parse_obj(new))

    print(news_list)
    context = {"result": news_list}
    return django.shortcuts.render(request, "form/news.html", context=context)


def view_news(request: django.http.HttpRequest, id: int):
    db_handle = db.get_db_handle()

    collection = db_handle[MONGODB_NEWS_COLLECTION_NAME]

    news = collection.find_one({"uuid": id})
    news_ = MongoForm.parse_obj(news)

    print(news_)
    context = {"result": news_}
    return django.shortcuts.render(request, "form/news.html", context=context)
