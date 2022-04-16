import django
import django.shortcuts


from form.form import ArticleForm, MONGODB_NEWS_COLLECTION_NAME, mongoForm
from utils import dbHandler
from model.predict import predict
from model.common import scaler, model_title, model_content, device, TOKENIZER
from cleaner.model import Cleaner

TOKENIZER = TOKENIZER
device = device
model_title = model_title
model_content = model_content
scaler = scaler

cleaner = Cleaner()


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
            db = dbHandler(
                db_name="news",
                host="mongodb",
                port=27017,
                username="root",
                password="ikkgIzSjBW",
            )
            db_handle = db.get_db_handle()

            collection = db_handle[MONGODB_NEWS_COLLECTION_NAME]

            outputs_title: float = 0.0
            outputs_content: float = 0.0

            title = form.cleaned_data.get("title")
            title = cleaner.map_dataframe(title, 0, 0.2, 0.2)[0]
            if title is not None:
                outputs_title = predict(
                    text=title,
                    model=model_title,
                    tokenizer=TOKENIZER,
                    scaler=scaler,
                    device=device,
                )[0][0]
            content = form.cleaned_data.get("article")
            content = cleaner.map_dataframe(content, 0, 0.2, 0.2)[0]
            if content is not None:
                outputs_content = predict(
                    text=content,
                    model=model_title,
                    tokenizer=TOKENIZER,
                    scaler=scaler,
                    device=device,
                )[0][0]

            label = 80 * outputs_content / 100 + 20 * outputs_title / 100
            entry = mongoForm(
                title=form.cleaned_data.get("title"),
                article=form.cleaned_data.get("article"),
                title_score=outputs_title,
                content_score=outputs_content,
                label=label,
            )

            try:
                collection.insert_one(entry.dict())
            except Exception:
                return django.http.HttpResponseRedirect("error")

            if label > 0.5:
                return django.http.HttpResponseRedirect("true")
            else:
                return django.http.HttpResponseRedirect("false")

    return django.shortcuts.render(request, "form/index.html", {"form": form})


def false(request: django.http.HttpRequest):
    return django.shortcuts.render(request, "form/false.html")


def true(request: django.http.HttpRequest):
    return django.shortcuts.render(request, "form/true.html")


def error(request: django.http.HttpRequest):
    return django.http.HttpResponseBadRequest("Server error")


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
