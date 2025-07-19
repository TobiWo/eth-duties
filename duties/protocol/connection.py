"""Module for protocol connection healthiness"""

from abc import ABC, abstractmethod
from asyncio import sleep
from datetime import datetime, timedelta, timezone
from logging import getLogger
from typing import List, Optional

from cli.arguments import ARGUMENTS
from cli.types import NodeConnectionProperties
from constants import endpoints, json, logging, program
from helper.general import get_correct_request_header
from requests import ConnectionError as RequestsConnectionError
from requests import ReadTimeout, Response, get


class NodeManager(ABC):
    """Abstract base class for managing node health and connections"""

    def __init__(self) -> None:
        self.healthy_nodes: List[NodeConnectionProperties] = []
        self._provided_nodes: List[NodeConnectionProperties] = []
        self._logger = getLogger()
        self._set_provided_nodes()

    def _set_provided_nodes(self) -> None:
        """Set provided nodes from arguments"""
        nodes = self._get_node_argument()
        if nodes:
            self._provided_nodes = list(set(nodes))

    async def update_node_health(self) -> None:
        """Update node healthiness in interval"""
        while True:
            self.update_node_health_once()
            await sleep(self._get_health_check_interval())

    def update_node_health_once(self) -> None:
        """Update node healthiness based on REST responses"""
        if self._provided_nodes:
            for node in self._provided_nodes:
                if self._check_node_health(node):
                    self._update_healthy_nodes("append", node)
                else:
                    self._update_healthy_nodes("remove", node)
            self._log_health_of_nodes()

    def _update_healthy_nodes(
        self, action: str, node: NodeConnectionProperties
    ) -> None:
        """Add or remove node to/from healthy nodes list

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

    @abstractmethod
    def _get_node_argument(self) -> List[NodeConnectionProperties]:
        """Get nodes from command line arguments"""

    @abstractmethod
    def _get_health_check_interval(self) -> int:
        """Get health check interval in seconds"""

    @abstractmethod
    def _check_node_health(self, node: NodeConnectionProperties) -> bool:
        """Check if a specific node is healthy"""

    @abstractmethod
    def _log_health_of_nodes(self) -> None:
        """Log the health status of nodes"""


class BeaconNode(NodeManager):
    """Check beacon node availability"""

    def __init__(self) -> None:
        self.is_any_node_healthy = False
        self.__last_used_beacon_node_info = datetime.now(timezone.utc) - timedelta(
            minutes=10
        )
        self.__last_all_healthy_nodes_log = datetime.now(timezone.utc) - timedelta(
            minutes=10
        )
        self.__last_used_beacon_node = "None"
        super().__init__()

    def _get_node_argument(self) -> List[NodeConnectionProperties]:
        """Get beacon nodes from command line arguments"""
        return ARGUMENTS.beacon_nodes if ARGUMENTS.beacon_nodes else []

    def _get_health_check_interval(self) -> int:
        """Get beacon node health check interval"""
        return program.SECONDS_UNTIL_BEACON_NODE_HEALTH_UPDATE

    def _check_node_health(self, node: NodeConnectionProperties) -> bool:
        """Check if beacon node is healthy"""
        try:
            response: Response = get(
                url=f"{node.url}{endpoints.NODE_HEALTH_ENDPOINT}",
                timeout=program.REQUEST_TIMEOUT,
            )
            return response.status_code == 200
        except (RequestsConnectionError, ReadTimeout):
            return False

    def _log_health_of_nodes(self) -> None:
        """Log healthiness of beacon nodes"""
        if len(self.healthy_nodes) == len(self._provided_nodes):
            self.__log_all_healthy_nodes()
        if not self.healthy_nodes:
            self.is_any_node_healthy = False
            self._logger.error(logging.NO_AVAILABLE_BEACON_NODE_MESSAGE)
        if self.healthy_nodes and len(self.healthy_nodes) != len(self._provided_nodes):
            for node in self._provided_nodes:
                if node not in self.healthy_nodes:
                    self._logger.error(
                        logging.ONE_NON_HEALTHY_BEACON_NODE_MESSAGE,
                        node.url,
                    )

    def __log_all_healthy_nodes(self) -> None:
        """Log all healthy beacon nodes message with throttling"""
        current_time = datetime.now(timezone.utc)
        if (
            current_time
            > self.__last_all_healthy_nodes_log
            + timedelta(
                minutes=program.MINUTES_UNTIL_ALL_HEALTHY_BEACON_NODE_CONNECTION_STRINGS_ARE_LOGGED
            )
            or not self.is_any_node_healthy
        ):
            self._logger.info(logging.ALL_HEALTHY_BEACON_NODES_MESSAGE)
            self.__last_all_healthy_nodes_log = current_time
            self.is_any_node_healthy = True

    async def update_beacon_node_health(self) -> None:
        """Update beacon node healthiness in interval"""
        await self.update_node_health()

    def update_beacon_node_health_once(self) -> None:
        """Update beacon node healthiness based on REST responses"""
        self.update_node_health_once()

    def get_healthy_beacon_node(self) -> Optional[NodeConnectionProperties]:
        """Get a healthy beacon node from the available nodes

        Returns:
            Optional[NodeConnectionProperties]: Connection properties for available beacon node, or None if no healthy nodes
        """
        current_time = datetime.now(timezone.utc)
        if self.healthy_nodes:
            selected_node = self.healthy_nodes[0]
            self.__log_used_beacon_node(current_time, selected_node.url)
            return selected_node
        return None

    def __log_used_beacon_node(self, time: datetime, node_url: str) -> None:
        """Log the used beacon node in dependence of specific events

        Args:
            time (datetime): Provided time which will be used to check if logging is needed
            node_url (str): Provided node url which is available
        """
        if (
            time
            > self.__last_used_beacon_node_info
            + timedelta(
                minutes=program.MINUTES_UNTIL_USED_BEACON_NODE_CONNECTION_STRING_IS_LOGGED
            )
            or not self.is_any_node_healthy
            or node_url != self.__last_used_beacon_node
        ):
            self._logger.info(logging.USED_BEACON_NODE_MESSAGE, node_url)
            self.__last_used_beacon_node_info = time
            self.is_any_node_healthy = True
            self.__last_used_beacon_node = node_url


class ValidatorNode(NodeManager):
    """Helper to check validator node healthiness"""

    def _get_node_argument(self) -> List[NodeConnectionProperties]:
        """Get validator nodes from command line arguments"""
        return ARGUMENTS.validator_nodes if ARGUMENTS.validator_nodes else []

    def _get_health_check_interval(self) -> int:
        """Get validator node health check interval"""
        return program.VALIDATOR_HEALTH_UPDATE_INTERVAL

    def _check_node_health(self, node: NodeConnectionProperties) -> bool:
        """Check if validator node is healthy"""
        try:
            header = get_correct_request_header(node)
            response = get(
                url=f"{node.url}{endpoints.FEERECIPIENT_ENDPOINT}",
                timeout=program.REQUEST_TIMEOUT,
                headers=header,
            )
            if response.status_code in (401, 403):
                self._logger.error(
                    logging.VALIDATOR_NODE_AUTHORIZATION_FAILED_MESSAGE,
                    node.url,
                )
                return False
            elif (
                json.RESPONSE_JSON_DATA_FIELD_NAME in response.json()
                or json.RESPONSE_JSON_MESSAGE_NAME in response.json()
            ):
                return True
            else:
                return False
        except RequestsConnectionError:
            return False

    def _log_health_of_nodes(self) -> None:
        """Log healthiness of validator nodes"""
        if len(self.healthy_nodes) == len(self._provided_nodes):
            self._logger.info(logging.ALL_HEALTHY_VALIDATOR_NODES_MESSAGE)
        if not self.healthy_nodes:
            self._logger.error(logging.NO_HEALTHY_VALIDATOR_NODES_MESSAGE)
        if self.healthy_nodes and len(self.healthy_nodes) != len(self._provided_nodes):
            for node in self._provided_nodes:
                if node not in self.healthy_nodes:
                    self.__log_unhealthy_node(node)

    async def update_validator_node_health(self) -> None:
        """Update validator node healthiness in interval"""
        await self.update_node_health()

    def update_validator_node_health_once(self) -> None:
        """Update validator node healthiness based on REST responses"""
        self.update_node_health_once()

    def __log_unhealthy_node(self, node: NodeConnectionProperties) -> None:
        """Log unhealthy node

        Args:
            node (NodeConnectionProperties): Node connection properties
        """
        self._logger.error(
            logging.ONE_NON_HEALTHY_VALIDATOR_NODE_MESSAGE,
            node.url,
        )
