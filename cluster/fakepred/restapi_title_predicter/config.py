import pydantic

from fakepred.uvicorn.config import UvicornConfig


class Config(pydantic.BaseModel):
    listen: UvicornConfig
