import django.forms
import pydantic

MONGODB_NEWS_COLLECTION_NAME = "news"

class ArticleForm(django.forms.Form):
    title = django.forms.CharField(label="Title", max_length=100, required=False)
    article = django.forms.CharField(label="Article", max_length=2500)

class mongoForm(pydantic.BaseModel):
    title: str
    article: str
    label: int # 1 true, 0 fake