import pydantic


class PredictRequest(pydantic.BaseModel):
    content: str = pydantic.Field(..., example="", title="Content to be prediected")


class PredictResponse(pydantic.BaseModel):
    score: float = pydantic.Field(
        ...,
        example="",
        title="Predicted content",
        description="Predicted score (float)",
    )
