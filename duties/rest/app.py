"""Module to start the rest api
"""

from cli.arguments import ARGUMENTS
from fetcher import get_logging_config
from rest.server import RestServer
from uvicorn import Config as UvicornConfig


def start_rest_server() -> None:
    """Starts the rest server with come configuration"""
    config = UvicornConfig(
        "rest.endpoints:app",
        host="127.0.0.1",
        port=5000,
        log_config=get_logging_config(ARGUMENTS.log),
    )
    rest_server = RestServer(config)
    rest_server.start()
