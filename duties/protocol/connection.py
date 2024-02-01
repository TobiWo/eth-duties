"""_summary_
"""

from datetime import datetime, timedelta, timezone
from logging import getLogger

from requests import ConnectionError as RequestsConnectionError
from requests import ReadTimeout, Response, get

from duties.cli.arguments import get_arguments
from duties.constants import endpoints, logging, program


# pylint: disable-next=too-few-public-methods
class BeaconNode:
    """Check beacon node availability"""

    def __init__(self) -> None:
        self.__arguments = get_arguments()
        self.is_any_node_healthy = True
        self.__last_beacon_node_call_error = datetime.now(timezone.utc) - timedelta(
            seconds=30
        )
        self.__last_used_beacon_node_info = datetime.now(timezone.utc) - timedelta(
            minutes=10
        )
        self.__last_used_beacon_node = self.__arguments.beacon_nodes[0]
        self.__logger = getLogger()

    def get_healthy_beacon_node(self, is_used_beacon_node_logged: bool) -> str:
        """Check provided beacon nodes for availability and logs respective events

        Returns:
            str: Connection string of available beacon node
        """
        current_time = datetime.now(timezone.utc)
        for index, node in enumerate(self.__arguments.beacon_nodes):
            if self.__is_node_healthy(node):
                self.__log_used_beacon_node(
                    current_time, node, is_used_beacon_node_logged
                )
                return node
            if (
                self.__arguments.beacon_nodes[index]
                == self.__arguments.beacon_nodes[-1]
            ):
                self.is_any_node_healthy = False
                self.__logger.error(logging.NO_AVAILABLE_BEACON_NODE_MESSAGE)
            self.__log_primary_node_is_down(current_time, node)
            self.__last_beacon_node_call_error = current_time
        return self.__arguments.beacon_nodes[0]

    def __is_node_healthy(self, node: str) -> bool:
        """Check if node is healthy

        Args:
            node (str): Node which will be checked

        Returns:
            bool: Is node available
        """
        try:
            response: Response = get(
                url=f"{node}{endpoints.NODE_HEALTH_ENDPOINT}",
                timeout=program.REQUEST_TIMEOUT,
            )
            if response.status_code == 200:
                return True
            return False
        except (RequestsConnectionError, ReadTimeout):
            return False

    def __log_used_beacon_node(
        self, time: datetime, node: str, is_logged: bool
    ) -> None:
        """Log the used beacon node in dependence of specific events

        Args:
            time (datetime): Provided time which will be used to check if logging is needed
            node (str): Provided node which is available
        """
        if (
            time
            > self.__last_used_beacon_node_info
            + timedelta(
                minutes=program.MINUTES_UNTIL_USED_BEACON_NODE_CONNECTION_STRING_IS_LOGGED_AGAIN
            )
            or not self.is_any_node_healthy
            or node != self.__last_used_beacon_node
        ) and is_logged:
            self.__logger.info(logging.USED_BEACON_NODE_MESSAGE, node)
            self.__last_used_beacon_node_info = time
            self.is_any_node_healthy = True
            self.__last_used_beacon_node = node

    def __log_primary_node_is_down(self, time: datetime, node: str) -> None:
        """Log if beacon node is down

        Args:
            time (datetime): Provided time which will be used to check if logging is needed
            node (str): Provided node which is not available
        """
        if time > self.__last_beacon_node_call_error + timedelta(
            seconds=program.SECONDS_UNTIL_BEACON_NODE_CALL_ERROR_IS_LOGGED_AGAIN
        ):
            if node == self.__arguments.beacon_nodes[0]:
                self.__logger.warning(logging.PRIMARY_BEACON_NODE_DOWN_MESSAGE, node)
            if len(self.__arguments.beacon_nodes) > 1:
                self.__logger.info(logging.TRYING_BACKUP_NODES_MESSAGE)
                self.__logger.info(logging.TRYING_BACKUP_NODES_MESSAGE)
