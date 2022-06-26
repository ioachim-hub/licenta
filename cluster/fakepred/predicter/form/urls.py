from django.urls import path

from form.views import (
    news,
    login,
    index,
    error,
    upload,
    fake_news,
    view_news,
    contribute,
    admin_login,
    validate_news,
    create_account,
    view_news_contribution,
)
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path("", index, name="index"),
    path("news", news, name="form"),
    path("form", index, name="form"),
    path("error", error, name="error"),
    path("upload", upload, name="upload"),
    path("news/<int:id>/", view_news, name="news"),
    path("fake_news", fake_news, name="fake_news"),
    path("contribution", login, name="contribution"),
    path("contribute", contribute, name="contribute"),
    path("admin_login", admin_login, name="admin_login"),
    path("validate_news", validate_news, name="validate_news"),
    path("create_account", create_account, name="create_account"),
    path(
        "news_contribution/<int:id>/", view_news_contribution, name="news_contribution"
    ),
]

urlpatterns += staticfiles_urlpatterns()
