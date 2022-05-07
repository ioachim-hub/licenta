from typing import Optional

import pydantic
import pandas as pd


class SiteConfig(pydantic.BaseModel):
    url: str
    type: str
    routes: list[str]


class Domain(pydantic.BaseModel):
    name: str
    articles: list[dict[str, str]] = []


class SiteData(pydantic.BaseModel):
    site: str
    domains: list[Domain] = []


class SearchedNews(pydantic.BaseModel):
    url: str
    text: str = ""
    slug: str = ""
    meta: str = ""
    title: str = ""
    is_similar: bool = False
    similarity_score_title: Optional[float] = None
    similarity_score_content: Optional[float] = None


class Entry(pydantic.BaseModel):
    site: str = ""
    domain: str = ""
    link: str = ""
    title: str = ""
    content: str = ""
    date: pd.Timestamp = pd.Timestamp.min
    label: int
    searched: int
    alike_news: Optional[list[Optional[SearchedNews]]] = []
    title_keywords: Optional[list[str]] = []
    content_keywords: Optional[list[str]] = []
