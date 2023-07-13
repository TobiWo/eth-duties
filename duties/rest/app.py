"""Module to start the rest api
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


def start_rest_server() -> None:
    """Starts the rest server with come configuration"""
    config = UvicornConfig(
        "rest.app:app",
        host="127.0.0.1",
        port=5000,
        log_config=get_logging_config(ARGUMENTS.log),
    )
    rest_server = RestServer(config)
    rest_server.start()
