"""Module to create the rest api server
"""

from fastapi import FastAPI
from uvicorn import Config as UvicornConfig

from duties.cli.arguments import get_arguments
from duties.initialize import get_logging_config
from duties.rest.core.server import RestServer
from duties.rest.router.main import router

__ARGUMENTS = get_arguments()

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
        host=__ARGUMENTS.rest_host,
        port=__ARGUMENTS.rest_port,
        log_config=get_logging_config(__ARGUMENTS.log),
    )
    rest_server = RestServer(config)
    return rest_server
    return rest_server
