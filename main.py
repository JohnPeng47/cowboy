import time
import logging
from os import path
from uuid import uuid1
from typing import Optional, Final
from contextvars import ContextVar

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from pydantic.error_wrappers import ValidationError

from sqlalchemy import inspect
from sqlalchemy.orm import scoped_session
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.routing import compile_path

from starlette.responses import Response, StreamingResponse, FileResponse
from starlette.staticfiles import StaticFiles


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse

import os
import uvicorn
from logging import getLogger
import yaml

from src.auth.views import auth_router

from src.database.core import engine, sessionmaker


async def not_found(request, exc):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": [{"msg": "Not Found."}]},
    )


exception_handlers = {404: not_found}


app = FastAPI(exception_handlers=exception_handlers, openapi_url="")

# local testing
origins = [
    "http://localhost:3000",  # Allow requests from your local frontend
    "http://localhost:5900",
    "http://localhost:10559",
    "http://18.221.129.100:8000",
    "http://172.31.32.87:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# def get_path_params_from_request(request: Request) -> str:
#     path_params = {}
#     for r in api_router.routes:
#         path_regex, path_format, param_converters = compile_path(r.path)
#         path = request["path"].removeprefix(
#             "/api/v1"
#         )  # remove the /api/v1 for matching
#         match = path_regex.match(path)
#         if match:
#             path_params = match.groupdict()
#     return path_params


def get_path_template(request: Request) -> str:
    if hasattr(request, "path"):
        return ",".join(request.path.split("/")[1:])
    return ".".join(request.url.path.split("/")[1:])


REQUEST_ID_CTX_KEY: Final[str] = "request_id"
_request_id_ctx_var: ContextVar[Optional[str]] = ContextVar(
    REQUEST_ID_CTX_KEY, default=None
)


def get_request_id() -> Optional[str]:
    return _request_id_ctx_var.get()


@app.middleware("http")
def db_session_middleware(request: Request, call_next):
    # request_id = str(uuid1())

    # we create a per-request id such that we can ensure that our session is scoped for a particular request.
    # see: https://github.com/tiangolo/fastapi/issues/726
    # ctx_token = _request_id_ctx_var.set(request_id)
    # path_params = get_path_params_from_request(request)

    # # if this call is organization specific set the correct search path
    # organization_slug = path_params.get("organization", "default")
    # request.state.organization = organization_slug

    # # Find out more about
    # schema = f"dispatch_organization_{organization_slug}"
    # # validate slug exists
    # schema_names = inspect(engine).get_schema_names()
    # if schema in schema_names:
    #     # add correct schema mapping depending on the request
    #     schema_engine = engine.execution_options(
    #         schema_translate_map={
    #             None: schema,
    #         }
    #     )
    # else:
    #     return JSONResponse(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         content={"detail": [{"msg": f"Unknown database schema name: {schema}"}]},
    #     )

    try:
        # session = scoped_session(sessionmaker(), scopefunc=get_request_id)
        session = sessionmaker(bind=engine)
        request.state.db = session()
        response = call_next(request)
    except Exception as e:
        raise e from None
    finally:
        request.state.db.close()

    # _request_id_ctx_var.reset(ctx_token)
    return response


# STATIC_DIR = "build"
# app.mount("/static", StaticFiles(directory=os.path.join(STATIC_DIR, "static")))


# @app.get("/")
# def read_root():
#     with open(os.path.join(STATIC_DIR, "index.html"), "r") as f:
#         content = f.read()
#         return HTMLResponse(content=content)


app.include_router(auth_router)


if __name__ == "__main__":
    uvicorn_version = uvicorn.__version__

    with open("uvicorn.yaml", "w") as f:
        config = {"uvicorn": {"no_color": True, "version": uvicorn_version}}
        yaml.dump(config, f)

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=3000,
        reload=True,
        # log_config="uvicorn.yaml",
    )