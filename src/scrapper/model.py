import pydantic


class SiteConfig(pydantic.BaseModel):
    url: str
    routes: list[str]


class Domain(pydantic.BaseModel):
    name: str
    articles: list[dict[str, str]] = []


class SiteData(pydantic.BaseModel):
    site: str
    domains: list[Domain] = []
