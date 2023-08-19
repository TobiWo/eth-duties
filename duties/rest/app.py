"""Module to create the rest api server
"""

from cli.arguments import ARGUMENTS
from fastapi import FastAPI
from fetcher import get_logging_config
from rest.core.server import RestServer
from rest.router.main import router
from uvicorn import Config as UvicornConfig

app = FastAPI(
    title="eth-duties REST API",
    description="REST endpoints exposed via eth-duties",
    version="v0.4.0",
)
app.include_router(router)


def create_rest_server() -> RestServer:
    """Create a FastAPI uvicorn server instance

    Returns:
        RestServer: FastAPI uvicorn server
    """
    config = UvicornConfig(
        "rest.app:app",
        host="127.0.0.1",
        port=ARGUMENTS.rest_port,
        log_config=get_logging_config(ARGUMENTS.log),
    )
    rest_server = RestServer(config)
    return rest_server
