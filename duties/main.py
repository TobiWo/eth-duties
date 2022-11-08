"""
Entrypoint for the simple cli tool to check for upcoming duties for one or many validators
"""

# pylint: disable=import-error

from argparse import Namespace
from time import sleep
from typing import List, Callable
from fetcher.fetcher import ValidatorDutyFetcher
from fetcher.data_types import ValidatorDuty
from fetcher.printer import print_time_to_next_duties
from helper.killer import GracefulKiller
from cli.cli import get_arguments
from colorama import init


__sort_duties: Callable[[ValidatorDuty], int] = lambda duty: duty.target_slot


def __fetch_validator_duties(
    arguments: Namespace,
    duty_fetcher: ValidatorDutyFetcher,
    duties: List[ValidatorDuty],
) -> List[ValidatorDuty]:
    # Check if both lists are empty
    current_slot = duty_fetcher.get_current_slot()
    if duties and duties[0].target_slot > current_slot:
        return duties
    next_attestation_duties: dict[int, ValidatorDuty] = {}
    if not arguments.omit_attestation_duties:
        next_attestation_duties = duty_fetcher.get_next_attestation_duties()
    next_proposing_duties = duty_fetcher.get_next_proposing_duties()
    duties = [
        duty
        for duties in [next_attestation_duties, next_proposing_duties]
        for duty in duties.values()
    ]
    duties.sort(key=__sort_duties)
    return duties


def __initialize_validator_duty_fetcher(
    arguments: Namespace, graceful_killer: GracefulKiller
) -> ValidatorDutyFetcher:
    if arguments.validators:
        return ValidatorDutyFetcher(
            arguments.beacon_node, arguments.validators, graceful_killer
        )
    return ValidatorDutyFetcher(
        arguments.beacon_node,
        [validator.strip() for validator in arguments.validator_file],
        graceful_killer,
    )


if __name__ == "__main__":
    init()
    killer = GracefulKiller()
    args = get_arguments()
    validator_duty_fetcher = __initialize_validator_duty_fetcher(args, killer)
    upcoming_duties: List[ValidatorDuty] = []
    while not killer.kill_now:
        upcoming_duties = __fetch_validator_duties(
            args, validator_duty_fetcher, upcoming_duties
        )
        print_time_to_next_duties(upcoming_duties, validator_duty_fetcher.genesis_time)
        sleep(15)
    print("\nHappy staking. See you for next maintenance \U0001F642 !")
