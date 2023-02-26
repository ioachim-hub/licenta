import pydantic


class UvicornConfig(pydantic.BaseModel):
    host: str = "127.0.0.1"
    port: pydantic.PositiveInt = 8000
