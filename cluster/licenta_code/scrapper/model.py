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


class Entry(pydantic.BaseModel):
    site: str = ""
    domain: str = ""
    link: str = ""
    title: str = ""
    content: str = ""
    label: int = 0
    date: pd.Timestamp = pd.Timestamp.min
