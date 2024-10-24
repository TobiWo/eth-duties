"""Identifier related helper module
"""

from multiprocessing.shared_memory import SharedMemory

from constants.program import ALL_VALIDATOR_IDENTIFIERS_SHARED_MEMORY_NAMES


def clean_shared_memory() -> None:
    """Releases shared memory instances"""
    for (
        validator_identifier_shared_memory_name
    ) in ALL_VALIDATOR_IDENTIFIERS_SHARED_MEMORY_NAMES:
        shared_memory_validator_identifiers = SharedMemory(
            validator_identifier_shared_memory_name, False
        )
        shared_memory_validator_identifiers.close()
        shared_memory_validator_identifiers.unlink()
