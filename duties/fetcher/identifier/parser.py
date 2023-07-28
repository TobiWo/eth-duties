"""Module for parsing provided validator identifiers
"""

from asyncio import run
from logging import getLogger
from multiprocessing.shared_memory import SharedMemory
from sys import exit as sys_exit
from typing import List

from cli.arguments import ARGUMENTS
from constants import logging, program
from fetcher.data_types import ValidatorIdentifier
from fetcher.identifier import core
from rest.core.types import HttpMethod

__LOGGER = getLogger()


def get_active_validator_indices() -> List[str]:
    """Create a list of active validator indices based on the provided user input

    Returns:
        List[str]: List of active validator indices based on the provided user input
    """
    complete_active_validator_identifiers = (
        core.read_validator_identifiers_from_shared_memory(
            program.ACTIVE_VALIDATOR_IDENTIFIERS_SHARED_MEMORY_NAME
        )
    )
    return list(complete_active_validator_identifiers.keys())


async def create_shared_active_validator_identifiers_at_startup() -> None:
    """Create validator identifiers based on the on-chain status in shared memory"""
    shared_active_validator_identifiers = SharedMemory(
        program.ACTIVE_VALIDATOR_IDENTIFIERS_SHARED_MEMORY_NAME, False
    )
    active_validator_identifiers = await core.fetch_active_validator_identifiers(
        __get_raw_validator_identifiers_from_cli()
    )
    core.write_validator_identifiers_to_shared_memory(
        shared_active_validator_identifiers, active_validator_identifiers
    )
    core.create_shared_active_validator_identifiers_with_alias()


def __get_raw_validator_identifiers_from_cli() -> dict[str, ValidatorIdentifier]:
    """Parse the validator identifiers provided by the user

    Returns:
        dict[str, ValidatorIdentifier]: Validator identifiers_
    """
    if ARGUMENTS.validators:
        return {
            core.get_validator_index_or_pubkey(
                None, core.create_raw_validator_identifier(str(validator))
            ): core.create_raw_validator_identifier(str(validator))
            for validator_list in ARGUMENTS.validators
            for validator in validator_list
        }
    return {
        core.get_validator_index_or_pubkey(
            None,
            core.create_raw_validator_identifier(
                str(validator).strip().replace("\n", "").replace("\r\n", "")
            ),
        ): core.create_raw_validator_identifier(
            str(validator).strip().replace("\n", "").replace("\r\n", "")
        )
        for validator in ARGUMENTS.validators_file
    }


async def update_shared_active_validator_identifiers(
    provided_raw_validator_identifiers: dict[str, ValidatorIdentifier],
    http_method: str,
) -> None:
    """Update the active validator identifiers in shared memory

    Args:
        provided_raw_validator_identifiers (dict[str, ValidatorIdentifier]): Provided validator
        identifiers by the user
        http_method (str): REST method
    """
    provided_active_validator_identifiers = (
        await core.fetch_active_validator_identifiers(
            provided_raw_validator_identifiers
        )
    )
    current_active_validator_identifiers = (
        core.read_validator_identifiers_from_shared_memory(
            program.ACTIVE_VALIDATOR_IDENTIFIERS_SHARED_MEMORY_NAME
        )
    )
    if http_method == HttpMethod.POST.value:
        current_active_validator_identifiers.update(
            provided_active_validator_identifiers
        )
    else:
        for identifier in provided_active_validator_identifiers.keys():
            current_identifier = current_active_validator_identifiers.get(identifier)
            if current_identifier:
                current_active_validator_identifiers.pop(identifier)
    shared_active_validator_identifiers = SharedMemory(
        program.ACTIVE_VALIDATOR_IDENTIFIERS_SHARED_MEMORY_NAME, False
    )
    core.write_validator_identifiers_to_shared_memory(
        shared_active_validator_identifiers, current_active_validator_identifiers
    )
    core.create_shared_active_validator_identifiers_with_alias()
    __set_update_flag_in_shared_memory()


def __set_update_flag_in_shared_memory() -> None:
    """Create a shared memory instance which is used in other processes to check whether validator
    identifiers got updated
    """
    try:
        SharedMemory(program.UPDATED_SHARED_MEMORY_NAME, True, 1).close()
    except FileExistsError:
        pass


try:
    SharedMemory(
        program.ACTIVE_VALIDATOR_IDENTIFIERS_SHARED_MEMORY_NAME,
        True,
        program.SIZE_OF_SHARED_MEMORY,
    )
    SharedMemory(
        program.ACTIVE_VALIDATOR_IDENTIFIERS_WITH_ALIAS_SHARED_MEMORY_NAME,
        True,
        program.SIZE_OF_SHARED_MEMORY,
    )
    run(create_shared_active_validator_identifiers_at_startup())
except KeyboardInterrupt:
    __LOGGER.error(logging.SYSTEM_EXIT_MESSAGE)
    sys_exit(1)
