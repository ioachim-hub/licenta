from typing import Optional

import datetime

import pydantic

import django.forms

MONGODB_NEWS_COLLECTION_NAME = "news"


class ArticleForm(django.forms.Form):
    title = django.forms.CharField(label="Title", max_length=200, required=False)
    content = django.forms.CharField(label="Content", max_length=10000, required=False)
    link = django.forms.CharField(label="Link", max_length=300, required=False)


class ArticleContributedForm(django.forms.Form):
    title = django.forms.CharField(label="Title", max_length=200, required=False)
    content = django.forms.CharField(label="Content", max_length=10000, required=False)
    link = django.forms.CharField(label="Link", max_length=300, required=False)
    label = django.forms.CharField(label="Label", max_length=5, required=True)


class LoginForm(django.forms.Form):
    username = django.forms.CharField(label="Username", max_length=200, required=True)
    password = django.forms.CharField(label="Password", max_length=10000, required=True)


class MongoForm(pydantic.BaseModel):
    uuid: int
    title: str
    content: str
    title_score: float
    content_score: float
    link: Optional[str] = None
    label: float  # 80% content_score + 20% title_score
    date: Optional[datetime.datetime] = None
