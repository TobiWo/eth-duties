"""Module for protocol connection healthiness
"""

from asyncio import sleep
from datetime import datetime, timedelta, timezone
from logging import getLogger
from typing import List

from cli.arguments import ARGUMENTS
from cli.types import NodeConnectionProperties
from constants import endpoints, json, logging, program
from helper.general import get_correct_request_header
from requests import ConnectionError as RequestsConnectionError
from requests import ReadTimeout, Response, get


# pylint: disable-next=too-few-public-methods
class BeaconNode:
    """Check beacon node availability"""

    def __init__(self) -> None:
        self.is_any_node_healthy = True
        self.__last_beacon_node_call_error = datetime.now(timezone.utc) - timedelta(
            seconds=30
        )
        self.__last_used_beacon_node_info = datetime.now(timezone.utc) - timedelta(
            minutes=10
        )
        self.__last_used_beacon_node = ARGUMENTS.beacon_nodes[0]
        self.__logger = getLogger()

    def get_healthy_beacon_node(
        self, is_used_beacon_node_logged: bool
    ) -> NodeConnectionProperties:
        """Check provided beacon nodes for availability and logs respective events

        Args:
            is_used_beacon_node_logged (bool): Should used beacon node be logged

        Returns:
            NodeConnectionProperties: Connection properties for available beacon node
        """
        current_time = datetime.now(timezone.utc)
        for index, node in enumerate(ARGUMENTS.beacon_nodes):
            if self.__is_node_healthy(node.url):
                self.__log_used_beacon_node(
                    current_time, node.url, is_used_beacon_node_logged
                )
                return node
            if ARGUMENTS.beacon_nodes[index] == ARGUMENTS.beacon_nodes[-1]:
                self.is_any_node_healthy = False
                self.__logger.error(logging.NO_AVAILABLE_BEACON_NODE_MESSAGE)
            self.__log_primary_node_is_down(current_time, node.url)
            self.__last_beacon_node_call_error = current_time
        return ARGUMENTS.beacon_nodes[0]

    def __is_node_healthy(self, node_url: str) -> bool:
        """Check if node is healthy

        Args:
            node_url (str): Node which will be checked

        Returns:
            bool: Is node available
        """
        try:
            response: Response = get(
                url=f"{node_url}{endpoints.NODE_HEALTH_ENDPOINT}",
                timeout=program.REQUEST_TIMEOUT,
            )
            if response.status_code == 200:
                return True
            return False
        except (RequestsConnectionError, ReadTimeout):
            return False

    def __log_used_beacon_node(
        self, time: datetime, node_url: str, is_logged: bool
    ) -> None:
        """Log the used beacon node in dependence of specific events

        Args:
            time (datetime): Provided time which will be used to check if logging is needed
            node_url (str): Provided node url which is available
            is_logged (bool): Should used beacon node be logged
        """
        if (
            time
            > self.__last_used_beacon_node_info
            + timedelta(
                minutes=program.MINUTES_UNTIL_USED_BEACON_NODE_CONNECTION_STRING_IS_LOGGED_AGAIN
            )
            or not self.is_any_node_healthy
            or node_url != self.__last_used_beacon_node
        ) and is_logged:
            self.__logger.info(logging.USED_BEACON_NODE_MESSAGE, node_url)
            self.__last_used_beacon_node_info = time
            self.is_any_node_healthy = True
            self.__last_used_beacon_node = node_url

    def __log_primary_node_is_down(self, time: datetime, node_url: str) -> None:
        """Log if beacon node is down

        Args:
            time (datetime): Provided time which will be used to check if logging is needed
            node_url (str): Provided node url which is not available
        """
        if time > self.__last_beacon_node_call_error + timedelta(
            seconds=program.SECONDS_UNTIL_BEACON_NODE_CALL_ERROR_IS_LOGGED_AGAIN
        ):
            if node_url == ARGUMENTS.beacon_nodes[0]:
                self.__logger.warning(
                    logging.PRIMARY_BEACON_NODE_DOWN_MESSAGE, node_url
                )
            if len(ARGUMENTS.beacon_nodes) > 1:
                self.__logger.info(logging.TRYING_BACKUP_NODES_MESSAGE)


class ValidatorNode:
    """Helper to check validator node healthiness"""

    def __init__(self) -> None:
        self.healthy_nodes: List[NodeConnectionProperties] = []
        self.__provided_nodes: List[NodeConnectionProperties] = []
        self.__set_provided_nodes()
        self.__logger = getLogger()

    def __set_provided_nodes(self) -> None:
        if ARGUMENTS.validator_nodes:
            self.__provided_nodes = list(set(ARGUMENTS.validator_nodes))

    async def update_validator_node_health(self) -> None:
        """Update validator node healthiness in interval"""
        while True:
            self.update_validator_node_health_once()
            await sleep(program.VALIDATOR_HEALTH_UPDATE_INTERVAL)

    def update_validator_node_health_once(self) -> None:
        """Update validator node healthiness based on REST responses"""
        if self.__provided_nodes:
            for node in self.__provided_nodes:
                try:
                    header = get_correct_request_header(node)
                    response = get(
                        url=f"{node.url}{endpoints.FEERECIPIENT_ENDPOINT}",
                        timeout=program.REQUEST_TIMEOUT,
                        headers=header,
                    )
                    if response.status_code == 401 or response.status_code == 403:
                        self.__logger.error(
                            logging.VALIDATOR_NODE_AUTHORIZATION_FAILED_MESSAGE,
                            node.url,
                        )
                        self.__update_healthy_nodes("remove", node)
                    elif (
                        json.RESPONSE_JSON_DATA_FIELD_NAME in response.json()
                        or json.RESPONSE_JSON_MESSAGE_NAME in response.json()
                    ):
                        self.__update_healthy_nodes("append", node)
                    else:
                        self.__update_healthy_nodes("remove", node)
                except RequestsConnectionError:
                    self.__update_healthy_nodes("remove", node)
            self.__log_health_of_nodes()

    def __update_healthy_nodes(
        self, action: str, node: NodeConnectionProperties
    ) -> None:
        """Add or remove validator node to/from healthy nodes list

        Args:
            action (str): Which action should be performed
            node (NodeConnectionProperties): Node connection properties
        """
        if action == "append":
            if node not in self.healthy_nodes:
                self.healthy_nodes.append(node)
        elif action == "remove":
            if node in self.healthy_nodes:
                self.healthy_nodes.remove(node)

    def __log_health_of_nodes(self) -> None:
        """Log healthiness of nodes"""
        if len(self.healthy_nodes) == len(self.__provided_nodes):
            self.__logger.info(logging.ALL_HEALTHY_VALIDATOR_NODES_MESSAGE)
        if not self.healthy_nodes:
            self.__logger.error(logging.NO_HEALTHY_VALIDATOR_NODES_MESSAGE)
            return None
        if len(self.healthy_nodes) != len(self.__provided_nodes):
            for node in self.__provided_nodes:
                if node not in self.healthy_nodes:
                    self.__log_unhealthy_node(node)

    def __log_unhealthy_node(self, node: NodeConnectionProperties) -> None:
        """Log unhealthy node

        Args:
            node (NodeConnectionProperties): Node connection properties
        """
        self.__logger.error(
            logging.ONE_NON_HEALTHY_VALIDATOR_NODE_MESSAGE,
            node.url,
        )
