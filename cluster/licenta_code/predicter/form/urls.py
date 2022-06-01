from django.urls import path

from form.views import index, upload, news, error, view_news
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path("", index, name="index"),
    path("form", index, name="form"),
    path("news", news, name="form"),
    path("upload", upload, name="upload"),
    path("error", error, name="error"),
    path("news/<int:id>/", view_news, name="news"),
]

urlpatterns += staticfiles_urlpatterns()
