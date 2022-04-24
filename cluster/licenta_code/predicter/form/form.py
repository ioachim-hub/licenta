from typing import Optional
import django.forms
import pydantic

MONGODB_NEWS_COLLECTION_NAME = "news"


class ArticleForm(django.forms.Form):
    title = django.forms.CharField(label="Title", max_length=200, required=False)
    content = django.forms.CharField(label="Content", max_length=4500)
    link = django.forms.CharField(label="Link", max_length=300, required=False)


class mongoForm(pydantic.BaseModel):
    uuid: int
    title: str
    content: str
    title_score: float
    content_score: float
    link: Optional[str] = None
    label: float  # 80% content_score + 20% title_score
