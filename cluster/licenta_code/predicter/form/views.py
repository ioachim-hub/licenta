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


db = dbHandler(
    db_name="news",
    host="mongodb",
    port=27017,
    username="root",
    password="ikkgIzSjBW",
)


def index(request: django.http.HttpRequest):
    collection = db.get_db_handle()[MONGODB_NEWS_COLLECTION_NAME]
    news = collection.find().limit(25).sort("uuid", -1)
    news_list = []
    for new in news:
        news_list.append(mongoForm.parse_obj(new))
    return django.shortcuts.render(
        request, "form/index.html", context={"result": news_list}
    )


@django.views.decorators.csrf.csrf_protect
def upload(request: django.http.HttpRequest):
    collection = db.get_db_handle()[MONGODB_NEWS_COLLECTION_NAME]
    news = collection.find().limit(25).sort("uuid", -1)
    news_list = []
    for new in news:
        news_list.append(mongoForm.parse_obj(new))
    print(news_list)
    form = ArticleForm()

    uuid = 1
    if len(news_list) > 0:
        uuid = news_list[0].uuid + 1
    # if this is a POST request we need to process the form data
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        form = ArticleForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            outputs_title: float = 0.5
            outputs_content: float = 0.5

            title = form.cleaned_data.get("title")
            if title is not None:
                title = cleaner.map_dataframe(title, 0, 0.2, 0.2)[0]
                outputs_title = predict(
                    text=title,
                    model=model_title,
                    tokenizer=TOKENIZER,
                    scaler=scaler,
                    device=device,
                )[0][0]
            content = form.cleaned_data.get("content")
            if content is not None:
                content = cleaner.map_dataframe(content, 0, 0.2, 0.2)[0]
                outputs_content = predict(
                    text=content,
                    model=model_title,
                    tokenizer=TOKENIZER,
                    scaler=scaler,
                    device=device,
                )[0][0]

            label = 80 * outputs_content / 100 + 20 * outputs_title / 100
            entry = mongoForm(
                uuid=uuid,
                title=form.cleaned_data.get("title"),
                content=form.cleaned_data.get("content"),
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

    return django.shortcuts.render(
        request, "form/index.html", context={"form": form, "result": news_list}
    )


def false(request: django.http.HttpRequest):
    return django.shortcuts.render(request, "form/false.html")


def true(request: django.http.HttpRequest):
    return django.shortcuts.render(request, "form/true.html")


def error(request: django.http.HttpRequest):
    return django.http.HttpResponseBadRequest("Server error")


def news(request: django.http.HttpRequest):
    db_handle = db.get_db_handle()

    collection = db_handle[MONGODB_NEWS_COLLECTION_NAME]

    news = collection.find().limit(25)
    news_list = []
    for new in news:
        news_list.append(mongoForm.parse_obj(new))

    print(news_list)
    context = {"result": news_list}
    return django.shortcuts.render(request, "form/news.html", context=context)


def view_news(request: django.http.HttpRequest, id: int):
    db_handle = db.get_db_handle()

    collection = db_handle[MONGODB_NEWS_COLLECTION_NAME]

    news = collection.find_one({"uuid": id})
    news_ = mongoForm.parse_obj(news)

    print(news_)
    context = {"result": news_}
    return django.shortcuts.render(request, "form/news.html", context=context)
