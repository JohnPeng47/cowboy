from typing import Optional, Final
from contextvars import ContextVar

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse

from sqlalchemy.orm import sessionmaker

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

import uvicorn
from logging import getLogger, Filter

from src.queue.core import TaskQueue
from src.auth.views import auth_router
from src.repo.views import repo_router
from src.test_modules.views import tm_router
from src.queue.views import task_queue_router
from src.test_gen.views import test_gen_router
from src.target_code.views import tgtcode_router
from src.experiments.views import exp_router
from src.health.views import health_router
from src.exceptions import CowboyRunTimeException

from src.extensions import init_sentry
from src.config import PORT

import uuid

from src.sync_repos import start_sync_thread
from src.database.core import engine
from src.token_registry import token_registry


log = getLogger(__name__)


async def not_found(request, exc):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": [{"msg": "Not Found."}]},
    )


class ExceptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except CowboyRunTimeException as e:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": [{"msg": str(e)}]},
            )
        except ValidationError as e:
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={"detail": e.errors()},
            )
        except Exception as e:
            log.exception(f"Unexpected error: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": [{"msg": "Internal server error"}]},
            )


def create_app(task_queue: TaskQueue, engine) -> FastAPI:
    exception_handlers = {404: not_found}
    app = FastAPI(exception_handlers=exception_handlers, openapi_url="/docs/openapi.json")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    class DBMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            try:
                request.state.session_id = str(uuid.uuid4())
                task_auth_token = request.headers.get("x-task-auth", None)
                if not task_auth_token or not task_auth_token in token_registry:
                    session = sessionmaker(bind=engine)
                    request.state.db = session()
                    request.state.db.id = str(uuid.uuid4())

                response = await call_next(request)
            except Exception as e:
                raise e from None
            finally:
                db = getattr(request.state, "db", None)
                if db:
                    db.close()
            return response

    class AddTaskQueueMiddleware(BaseHTTPMiddleware):
        async def dispatch(
            self, request: Request, call_next: RequestResponseEndpoint
        ) -> Response:
            request.state.task_queue = task_queue
            response = await call_next(request)
            return response

    app.add_middleware(ExceptionMiddleware)
    app.add_middleware(DBMiddleware)
    app.add_middleware(AddTaskQueueMiddleware)

    app.include_router(auth_router)
    app.include_router(repo_router)
    app.include_router(tm_router)
    app.include_router(task_queue_router)
    app.include_router(test_gen_router)
    app.include_router(tgtcode_router)
    app.include_router(exp_router)
    app.include_router(health_router)

    return app


def create_server(app: FastAPI, host, port, workers = 2):
    # init_sentry()

    # start the repo sync thread
    # Session = sessionmaker(bind=engine)
    # db_session = Session()
    # start_sync_thread(db_session, task_queue)

    class CustomFilter(Filter):
        def filter(self, record):
            return "GET /task/get" not in record.getMessage()

    # Move the logger configuration into a function that will be called for each worker
    async def configure_worker_logger():
        uvicorn_logger = getLogger("uvicorn.access")
        uvicorn_logger.addFilter(CustomFilter())

    app = create_app(TaskQueue(), engine)

    # Configure the logging when the worker starts
    config = uvicorn.Config(
        app,
        host=host, 
        port=port,
        workers=workers,
        callback_notify=configure_worker_logger # This will run for each worker
    )
    server = uvicorn.Server(config)
    server.run()
    

if __name__ == "__main__":
    app = create_app(TaskQueue(), engine)
    create_server(app, "0.0.0.0", int(PORT))