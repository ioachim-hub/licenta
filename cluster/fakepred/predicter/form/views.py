from typing import Optional

import json
import requests  # type: ignore
import datetime
import dataclasses

import django
import django.shortcuts
import django.contrib.auth
import django.contrib.auth.models


from form.form import (
    ArticleContributedForm,
    ArticleForm,
    MONGODB_NEWS_COLLECTION_NAME,
    LoginForm,
    MongoForm,
)
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
    status: str = ""
    user: str = ""


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

    context = {"result": news_list}
    return django.shortcuts.render(request, "form/news.html", context=context)


def view_news(request: django.http.HttpRequest, id: int):
    db_handle = db.get_db_handle()

    collection = db_handle[MONGODB_NEWS_COLLECTION_NAME]

    news = collection.find_one({"uuid": id})
    news_ = MongoForm.parse_obj(news)

    context = {"result": news_}
    return django.shortcuts.render(request, "form/news.html", context=context)


def view_news_contribution(request: django.http.HttpRequest, id: int):
    db_handle = db.get_db_handle()

    collection = db_handle[MONGODB_NEWS_COLLECTION_NAME]

    news = collection.find_one({"uuid": id})
    news_ = MongoForm.parse_obj(news)

    context = {"result": news_}
    return django.shortcuts.render(
        request, "form/news_contribution.html", context=context
    )


def validate_news(request: django.http.HttpRequest):
    if request.method == "POST" and request.is_ajax():
        id: int = int(request.POST.get("id"))
        collection = db.get_db_handle()[MONGODB_NEWS_COLLECTION_NAME]
        collection.update_one(
            filter={"uuid": id},
            update={
                "$set": {
                    "title_score": 1,
                    "content_score": 1,
                    "label": 1,
                }
            },
        )
        return django.http.HttpResponse(
            json.dumps({"status": "ok"}), content_type="application/json"
        )


def fake_news(request: django.http.HttpRequest):
    if request.method == "POST" and request.is_ajax():
        id: int = int(request.POST.get("id"))
        collection = db.get_db_handle()[MONGODB_NEWS_COLLECTION_NAME]
        collection.update_one(
            filter={"uuid": id},
            update={
                "$set": {
                    "title_score": 0,
                    "content_score": 0,
                    "label": 0,
                }
            },
        )
        return django.http.HttpResponse(
            json.dumps({"status": "ok"}), content_type="application/json"
        )


@django.views.decorators.csrf.csrf_protect
def login(request: django.http.HttpRequest):
    collection = db.get_db_handle()[MONGODB_NEWS_COLLECTION_NAME]
    news = collection.find().limit(25).sort("uuid", -1)
    news_list = []
    for new in news:
        news_list.append(MongoForm.parse_obj(new))
    response: Response = Response(news_list=news_list)

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user = django.contrib.auth.authenticate(
                request=request,
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
            )
            response.user = form.cleaned_data["username"]
            if user is not None:
                django.contrib.auth.login(request, user)
                return django.shortcuts.render(
                    request, "form/contribute.html", context={"result": response}
                )
            else:
                response.status = "User is not found"
                return django.shortcuts.render(
                    request, "form/index.html", context={"result": response}
                )

    return django.shortcuts.render(
        request, "form/index.html", context={"result": response}
    )


@django.views.decorators.csrf.csrf_protect
def admin_login(request: django.http.HttpRequest):

    if request.method == "POST":
        form = LoginForm(request.POST)
        try:
            user = django.contrib.auth.models.User.objects.create_user(
                "admin123", "ioachim.lihor@gmail.com", "admin123!@#"
            )
        except Exception as e:
            print(e)
        if form.is_valid():
            if (
                form.cleaned_data["username"] == "admin123"
                and form.cleaned_data["password"] == "admin123!@#"
            ):
                username = form.cleaned_data["username"]
                password = form.cleaned_data["password"]
                user = django.contrib.auth.authenticate(
                    request, username=username, password=password
                )
                if user is not None:
                    django.contrib.auth.login(request, user)
                    return django.shortcuts.render(
                        request,
                        "form/admin_create_accounts.html",
                        context={"status": ""},
                    )
                else:
                    return django.shortcuts.render(
                        request,
                        "form/admin_login.html",
                        context={"status": "User is not found"},
                    )
            else:
                return django.shortcuts.render(
                    request,
                    "form/admin_login.html",
                    context={
                        "status": "Invalid credentials",
                    },
                )
    return django.shortcuts.render(
        request, "form/admin_login.html", context={"status": ""}
    )


@django.views.decorators.csrf.csrf_protect
def create_account(request: django.http.HttpRequest):
    collection = db.get_db_handle()[MONGODB_NEWS_COLLECTION_NAME]
    news = collection.find().limit(25).sort("uuid", -1)
    news_list = []
    for new in news:
        news_list.append(MongoForm.parse_obj(new))

    response: Response = Response(news_list=news_list)
    if request.method == "POST":
        form = LoginForm(request.POST)
        if request.user.is_authenticated:
            if form.is_valid():
                username = form.cleaned_data["username"]
                password = form.cleaned_data["password"]

                try:
                    user = django.contrib.auth.models.User.objects.create_user(
                        username=username, password=password
                    )
                    user.save()
                except Exception as e:
                    return django.shortcuts.render(
                        request,
                        "form/admin_create_accounts.html",
                        context={"status": e},
                    )
                return django.shortcuts.render(
                    request,
                    "form/admin_create_accounts.html",
                    context={"status": "Account created"},
                )
        else:
            response.status = "You are not logged in as admin"
            return django.shortcuts.render(
                request, "form/index.html", context={"result": response}
            )
    return django.shortcuts.render(
        request, "form/admin_create_accounts.html", context={"status": ""}
    )


@django.views.decorators.csrf.csrf_protect
def contribute(request: django.http.HttpRequest):
    collection = db.get_db_handle()[MONGODB_NEWS_COLLECTION_NAME]
    news = collection.find().sort("uuid", -1)
    news_list = []
    for new in news:
        news_list.append(MongoForm.parse_obj(new))
    form = ArticleContributedForm()
    response: Response = Response(news_list=news_list)

    uuid = 1
    if request.user.is_authenticated:
        response.user = request.user.username
        if len(news_list) > 0:
            uuid = news_list[0].uuid + 1
        # if this is a POST request we need to process the form data
        if request.method == "POST":
            # create a form instance and populate it with data from the request:
            form = ArticleContributedForm(request.POST)
            # check whether it's valid:
            if form.is_valid():
                if (
                    form.cleaned_data.get("title") != ""
                    and form.cleaned_data.get("content") != ""
                ):
                    link = form.cleaned_data.get("link")

                    label = 1 if form.cleaned_data.get("label") == "Valid" else 0
                    outputs_title = label
                    outputs_content = label

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

                    entry_similar = collection.find_one(
                        {"title": form.cleaned_data.get("title")}
                    )
                    if entry_similar is None:
                        try:
                            collection.insert_one(entry.dict())
                            response.status = "NEWS INSERTED"
                        except Exception:
                            return django.http.HttpResponseRedirect("error")
                    else:
                        response.status = "NEWS ALREADY INSERTED"
                        return django.shortcuts.render(
                            request,
                            "form/contribute.html",
                            context={"form": form, "result": response},
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
                        "form/contribute.html",
                        context={"form": form, "result": response},
                    )

        return django.shortcuts.render(
            request, "form/contribute.html", context={"form": form, "result": response}
        )
    else:
        return django.shortcuts.render(
            request, "form/index.html", context={"form": form, "result": response}
        )
