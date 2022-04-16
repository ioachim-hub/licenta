from django.urls import path

from form.views import index, true, false, upload, news, error
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path("", index, name="index"),
    path("form", index, name="form"),
    path("news", news, name="form"),
    path("upload", upload, name="upload"),
    path("true", true, name="true"),
    path("false", false, name="false"),
    path("error", error, name="error"),
]

urlpatterns += staticfiles_urlpatterns()
