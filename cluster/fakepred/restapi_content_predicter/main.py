import logging

import pydantic
import fastapi
import fastapi.responses
import uvicorn


from fakepred.utils.common import get_settings_path

from fakepred.restapi_content_predicter.config import Config
from fakepred.restapi_content_predicter.state import RESTState
from fakepred.restapi_content_predicter.models import PredictRequest, PredictResponse


async def pydantic_validation_error_handler(
    request: fastapi.Request, exc: pydantic.ValidationError
) -> fastapi.responses.JSONResponse:
    logging.error(
        f"pydantic_validation_error_handler request: {request}, exception: {exc}"
    )

    return fastapi.responses.JSONResponse(
        status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "python code error", "exception": repr(exc)},
    )


router = fastapi.APIRouter()
reststate: RESTState = RESTState()


def get_app_fastapi(cfg: Config) -> fastapi.FastAPI:
    logging.basicConfig(level=logging.INFO)

    app = fastapi.FastAPI(
        title="Content predicter RESTApi",
        version="1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        exception_handlers={
            pydantic.ValidationError: pydantic_validation_error_handler,
        },
    )

    async def app_on_startup() -> None:
        logging.info("app_on_startup")

    async def app_on_shutdown() -> None:
        logging.info("app_on_shutdown")

    app.add_event_handler("startup", app_on_startup)
    app.add_event_handler("shutdown", app_on_shutdown)

    app.include_router(router)

    return app


@router.get("/health")
def get_health() -> fastapi.Response:
    return fastapi.Response(status_code=fastapi.status.HTTP_200_OK)


@router.post(
    "/predict",
    response_model=PredictResponse,
    responses={fastapi.status.HTTP_400_BAD_REQUEST: {"description": "Invalid input"}},
)
def predict(
    req: PredictRequest,
    request: fastapi.Request,
    response: fastapi.Response,
) -> PredictResponse:
    logging.info(f"predict request: {req}")
    score = reststate.predict(req.content)
    res = PredictResponse(score=score)
    return res


def main() -> None:
    cfg_path = get_settings_path()
    cfg = Config.parse_file(cfg_path)
    app = get_app_fastapi(cfg)

    uvicorn_cfg = cfg.listen
    uvicorn.run(app, host=uvicorn_cfg.host, port=uvicorn_cfg.port)


if __name__ == "__main__":
    main()
