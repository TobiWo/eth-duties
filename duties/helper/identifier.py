"""Identifier related helper module"""

from multiprocessing.shared_memory import SharedMemory
from os import environ

from constants.program import (
    ALL_VALIDATOR_IDENTIFIERS_SHARED_MEMORY_NAMES,
    IS_SHARED_MEMORY_OWNER,
    RANDOM_NUMBERS,
    SHARED_MEMORY_IDS_ENVIRONMENT_VARIABLE,
    SHARED_MEMORY_IDS_SEPARATOR,
    UPDATED_SHARED_MEMORY_NAME,
)


def open_shared_memory(name: str, create: bool = False, size: int = 0) -> SharedMemory:
    """Opens or creates a shared memory instance of this eth-duties instance

    Only the process which owns the shared memory instances registers them at the
    resource tracker. Otherwise, the tracker of a child process would report the
    instances as leaked and unlink them when the child process terminates.

    Args:
        name (str): Name of the shared memory instance
        create (bool, optional): Whether to create a new shared memory instance. Defaults to False. # pylint: disable=line-too-long
        size (int, optional): Size in bytes when creating a new instance. Defaults to 0.

    Returns:
        SharedMemory: Shared memory instance
    """
    return SharedMemory(name, create, size, track=IS_SHARED_MEMORY_OWNER)


def share_shared_memory_ids_with_child_processes() -> None:
    """Exposes the shared memory ids of this instance to child processes

    Child processes which are not forked (start methods spawn and forkserver) re-import
    all modules and would otherwise create their own random shared memory ids.
    """
    environ[SHARED_MEMORY_IDS_ENVIRONMENT_VARIABLE] = SHARED_MEMORY_IDS_SEPARATOR.join(
        str(shared_memory_id) for shared_memory_id in RANDOM_NUMBERS
    )


def clean_shared_memory() -> None:
    """Releases shared memory instances"""
    for (
        validator_identifier_shared_memory_name
    ) in ALL_VALIDATOR_IDENTIFIERS_SHARED_MEMORY_NAMES:
        shared_memory_validator_identifiers = open_shared_memory(
            validator_identifier_shared_memory_name
        )
        shared_memory_validator_identifiers.close()
        shared_memory_validator_identifiers.unlink()
    __clean_unprocessed_update_flag()


def __clean_unprocessed_update_flag() -> None:
    """Releases the update flag if it was set but not yet processed by the main process"""
    try:
        update_flag = open_shared_memory(UPDATED_SHARED_MEMORY_NAME)
    except FileNotFoundError:
        return
    update_flag.close()
    update_flag.unlink()
