"""Module to start the rest api
"""

import socket as sock
from logging import getLogger

from cli.arguments import ARGUMENTS
from constants import logging
from fastapi import FastAPI
from fetcher import get_logging_config
from rest.core.server import RestServer
from rest.router.main import router
from uvicorn import Config as UvicornConfig

__LOGGER = getLogger()

app = FastAPI(
    title="eth-duties REST API",
    description="REST endpoints exposed via eth-duties",
    version="v0.4.0",
)
app.include_router(router)


def start_rest_server() -> None:
    """Starts the rest server with come configuration"""
    if not __is_port_in_use():
        config = UvicornConfig(
            "rest.app:app",
            host="127.0.0.1",
            port=ARGUMENTS.rest_port,
            log_config=get_logging_config(ARGUMENTS.log),
        )
        rest_server = RestServer(config)
        rest_server.start()


def __is_port_in_use() -> bool:
    """Check if defined port for rest server is already in use

    Returns:
        bool: Is defined port already in use
    """
    socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
    destination = ("127.0.0.1", ARGUMENTS.rest_port)
    connection_result = socket.connect_ex(destination)
    if connection_result == 0:
        __LOGGER.error(logging.PORT_ALREADY_IN_USAE_MESSAGE, ARGUMENTS.rest_port)
        socket.close()
        return True
    socket.close()
    return False
