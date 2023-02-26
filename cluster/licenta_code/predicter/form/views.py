import random

import django
import django.shortcuts


from form.form import ArticleForm, MONGODB_NEWS_COLLECTION_NAME, mongoForm
from utils import dbHandler


def index(request: django.http.HttpRequest):
    return django.shortcuts.render(request, "form/index.html")


@django.views.decorators.csrf.csrf_protect
def upload(request: django.http.HttpRequest):
    # if this is a POST request we need to process the form data
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        form = ArticleForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            label = random.randint(0, 100) % 2
            db = dbHandler(
                db_name="news",
                host="mongodb",
                port=27017,
                username="root",
                password="ikkgIzSjBW",
            )
            db_handle = db.get_db_handle()

            collection = db_handle[MONGODB_NEWS_COLLECTION_NAME]

            entry = mongoForm(
                title=form.cleaned_data.get("title"),
                article=form.cleaned_data.get("article"),
                label=label,
            )

            try:
                collection.insert_one(entry.dict())
            except Exception:
                return django.http.HttpResponseBadRequest("Stirea este falsa")

            if label == 1:
                return django.http.HttpResponseRedirect("true")
            else:
                return django.http.HttpResponseRedirect("false")

    return django.shortcuts.render(request, "form/index.html", {"form": form})


def false(request: django.http.HttpRequest):
    return django.shortcuts.render(request, "form/false.html")


def true(request: django.http.HttpRequest):
    return django.shortcuts.render(request, "form/true.html")


def news(request: django.http.HttpRequest):
    db = dbHandler(
        db_name="news",
        host="mongodb",
        port=27017,
        username="root",
        password="ikkgIzSjBW",
    )
    db_handle = db.get_db_handle()

    collection = db_handle[MONGODB_NEWS_COLLECTION_NAME]

    news = collection.find().limit(25)
    news_list = []
    for new in news:
        news_list.append(mongoForm.parse_obj(new))

    print(news_list)
    context = {"result": news_list}
    return django.shortcuts.render(request, "form/news.html", context=context)
