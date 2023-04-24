<!-- markdownlint-disable MD033 -->

# eth-duties

![python-badge](https://img.shields.io/badge/python-3.10-brightgreen)
![poetry-badge](https://img.shields.io/badge/poetry-1.3.1-brightgreen)
![black-badge](https://img.shields.io/badge/black-22.10.0-black)

ETH-duties logs upcoming validator duties to the console in order to find the best maintenance period for your validator(s). In general the tool was developed to mainly help home stakers but it still can be used on a larger scale (see [usage](#usage) examples).

**Note on docker `latest` tag: Currently the docker image tag `latest` refers to the latest changes on the `main` branch. Please be aware of that if you decide to use this tag.**

## Table of Contents

* [Consensus client compatibility](#consensus-client-compatibility)
* [Configuration](#configuration)
  * [--mode](#--mode)
    * [cicd-exit](#cicd-exit)
    * [cicd-wait](#cicd-wait)
    * [exit](#exit)
* [What to expect](#what-to-expect)
  * [Examples](#examples)
* [Binary/Executable Compatibility](#binary-executable-compatibility)
* [Usage](#usage)
* [Contribute](#contribute)
  * [Requirements](#requirements)
  * [Installation](#installation)
* [Build on your own](#build-on-your-own)
* [Docker](#docker)
  * [Run in Docker](#run-in-docker)
  * [Docker compose](#docker-compose)
* [Donate](#donate)
  * [Full disclosure](#full-disclosure)

## Consensus client compatibility

| client | tested | compatible |
|  --- |  --- | --- |
| prysm | :heavy_check_mark: | :heavy_check_mark: |
| lighthouse | :heavy_check_mark: | :heavy_check_mark: |
| teku | :heavy_check_mark: | :heavy_check_mark: |
| nimbus | :heavy_check_mark: | :heavy_check_mark: |
| lodestar | :heavy_check_mark: | :heavy_check_mark: |

## Configuration

Most of the available flags are self explanatory. However, some may not be that obvious. Those flags are described in detail in the following chapter.

For all available cli flags please call `eth-duties --help` (see usage examples for further details).

### --mode

The default running mode of `eth-duties` is logging duties to the console (specified with value `log`). However, professional node operators might leverage the tool in their cicd pipelines to e.g. prevent an unintentional client update when your validator is right before proposing a block or part of the sync committee. This is where the different `cicd` modes come into play. You can make your deployment job dependent from the `eth-duties` job so that the deployment job will only run when `eth-duties` exits gracefully with `exit code 0`.

**Note** If you do not omit attestation duties with `--omit-attestation-duties` these are also considered as valid duties for the cicd modes.

#### cicd-exit

This mode results in a one time check whether one of your supplied validators has an upcoming duty. If there is an upcoming duty the tool exits with `exit code 1`. If there is none the tool exits with `exit code 0`.

#### cicd-wait

This mode results in an ongoing process (similar to the standard behavior) where `eth-duties` checks for upcoming duties until there is none. If there will be no upcoming duty the application exits with `exit code 0`. Compared to the standard logging behavior this process only runs for a certain amount of time (specified with flag `--mode-cicd-waiting-time` (default: 780 seconds, approx. 2 epochs)). If this timeframe ends, `eth-duties` exits with `exit code 1`.

#### exit

This mode results in an immediate graceful exit with `exit code 0` without checking for duties. The rationale behind this flag is the following: If your deployment job will not run because of upcoming duties but you need to force an update for whatever reason you can use the mode `exit`. I'm not an expert in github pipelines but in gitlab you can prefill environment variables when you start a pipeline manually via the web ui. This way you don't need to adapt your pipeline code but just restart a pipeline with the `exit` mode. In general how to setup your pipelines is out of scope of this documentation. For more information please check the respective platform documentation. For gitlab this would be [the following website](https://docs.gitlab.com/ee/ci/pipelines/index.html#prefill-variables-in-manual-pipelines).

### --validators

This flag is self-explanatory in general but you need to respect the following separation rules:

* Validator identifiers can be separated by comma or space e.g.:
  * `--validators 123 456 --validators 678 999`
  * `--validators 123,456 --validators 678,999`
* If you provide a validator identifier with an alias you need to wrap the whole string of one identifier-alias-pair in quotes or double quotes e.g.:
  * `--validators "123;val1" "456;val2" --validators 678 999` or
  * `--validators "123;val1","456;val2" --validators 678,999`

**Note: Wrapping an identifier-alias-pair in quotes or double quotes is not true for a `docker-compose`. Please check the example [compose](docker/compose.yaml).**

## What to expect

Beside the actual functionality of logging upcoming duties I added some kind of UX in form of color coding.

The color coding comprises of:

| Color | Description |
| --- | --- |
| GREEN | Indicates upcoming block proposer duties |
| YELLOW | The upcoming duty will be performed in less than 2 minutes **or** your validator was chosen to be part in the next sync committee |
| RED | The upcoming duty will be performed in less than 1 minute **or** your validator is part of the current sync committee |

### Examples

1. Attestion duties for some validators ![attestations](./img/attestations.PNG)
1. Block proposing duties for some validators ![proposing](./img/proposing.PNG)
1. Sync committee duties for some validators ![sync_committee](./img/sync_committee.PNG)

## Binary (executable) Compatibility

**Note: The linux binary will only work on Ubuntu 22.04. That's due to the fact how pyinstaller bundles everything together for a specific OS. Since Ubuntu 20.04 is probably still widely in usage I will add another pipeline to build the binary specifically for Ubuntu 20.04. I will also rename the final artifact for better clarity.**

| OS | Tested | Works |
| --- | --- | --- |
| MacOS 11 | True | True |
| MacOS 12 | True | True |
| Ubuntu 20.04 | True | False |
| Ubuntu 22.04 | True | True |
| Windows 7 | False | - |
| Windows 10 | True | True |
| Windows 11 | False | - |

I would love to get feedback from the community, especially for the missing OS I couldn't test.

## Usage

Just download the artifact for your OS and start optimizing your validator maintenance periods. The example commands are based on calls on the linux binary (don't forget to make it executable).

1. Print the help:

    ```bash
    ./eth-duties --help
    ```

1. Print upcoming duties for two validators while connecting to a local beacon client:

    ```bash
    ./eth-duties \
    --validators <VALIDATOR_INDEX_1> <VALIDATOR_INDEX_2> \
    --beacon-node http://localhost:5052
    ```

1. Print upcoming duties for multiple validators using different identifiers while connecting to a local beacon client:

    ```bash
    # You can mix up indices and pubkeys as you like
    # You can add the flag '--validators' multiple times
    ./eth-duties \
    --validators <VALIDATOR_INDEX_1> <VALIDATOR_INDEX_2> \
    --validators <VALIDATOR_PUBKEY_3> <VALIDATOR_INDEX_4> \
    --beacon-node http://localhost:5052
    ```

1. Print upcoming duties for multiple validators using an alias for some of the provided validators while connecting to a local beacon client:

    ```bash
    # If you want to set an alias for a validator pubkey or index you need to separate the index/pubkey from the alias with an ';'
    # Furthermore you need to put the expression in quotes or double quotes 
    ./eth-duties \
    --validators "<VALIDATOR_INDEX_1>;VALIDATOR_1" <VALIDATOR_INDEX_2> \
    --validators "<VALIDATOR_PUBKEY_3>;VALIDATOR_3" <VALIDATOR_INDEX_4> \
    --beacon-node http://localhost:5052
    ```

1. Print upcoming duties for validators which indices/pubkeys are located in a file:

    ```bash
    # Mixing indices and pubkeys and/or adding aliases is also supported in files
    # Note that you do not need to put '<INDEX_OR_PUBKEY>;<ALIAS>' in quotes or double quotes in your validators file
    ./eth-duties \
    --validators-file <PATH_TO_VALIDATOR_FILE> \
    --beacon-node http://localhost:5052
    ```

1. Print upcoming validator duties but omit attestation duties:

    ```bash
    # Note: If you provide more than 50 validators, attestation related logs are omitted by default
    # This can be changed with '--max-attestation-duty-logs'
    ./eth-duties \
    --validators-file <PATH_TO_VALIDATOR_FILE> \
    --beacon-node http://localhost:5052 \
    --omit-attestation-duties
    ```

## Contribute

If you want to contribute you need to setup the project which is described in this section.

### Requirements

* `Python 3.10`

The tool explicitly needs `Python 3.10` as I use a feature which was just introduced with this version.

`Python 3.11` will not work currently as the dependencies weren't updated for that version yet.

In general it is recommended to work with virtual environments instead of a global python installation. This is out of scope of this documentation.

### Installation

Dependencies are organized and managed using poetry. Poetry itself needs `Python 3.7` or later.

My personal workflow to manage virtual environments is to use [miniconda/Anaconda](https://docs.conda.io/en/latest/miniconda.html), therefore the steps described are based on this toolchain.

1. Navigate to the root folder of the repository
1. Create new conda environment with poetry

    ```bash
    conda env create -f poetry_env.yaml
    ```

1. Activate your newly created conda environment

    ```bash
    conda activate poetry-py310
    ```

1. List your Python environments with poetry

    ```bash
    poetry env info
    # You will receive a Python System and Virtualenv output
    ```

1. Create a separate poetry virtual env

    ```bash
    # Create a poetry virtual env while using the executable/binary path of the virtualenv output of the command before
    poetry env use <PATH_TO_PYTHON_EXECUTABLE_OF_VIRTUALENV>
    ```

1. Install dependencies

    ```bash
    # Installs all dependencies
    poetry install

    # Installs only dependencies for running the application
    poetry install --only main
    ```

## Build on your own

You can build the binary/executable on your own. This will work out of the box if you installed all dev dependencies (see [installation](#installation)).

Note: Pyinstaller uses the OS where it runs on to build the respective artefact. So if you are on a windows machine you will build an executable of eth-duties.

As always you need to navigate to the root folder of this repository first. Make sure you are in the correct virtual environment where you installed the dependencies.

1. Build Windows executable

    ```cmd
    poetry run pyinstaller --clean --onefile --add-data config;config --name eth-duties .\duties\main.py
    ```

1. Build Linux or MacOS binary

    ```bash
    poetry run pyinstaller --clean --onefile --add-data config:config --name eth-duties ./duties/main.py
    ```

## Docker

### Run in Docker

1. Build image

    ```bash
    docker build -t tobiwo/eth-duties:latest -f docker/dockerfile .
    ```

1. Run container using space separation for --validators

    ```bash
    docker run \
    --rm \
    --name eth-duties \
    tobiwo/eth-duties:latest \
    --validators 123456 456789 \
    --validators 0x98... \
    --validators "111;My_Validator" "222;Validator2" \
    --beacon-node http://localhost:5052
    ```

1. Run container on boot using comma separation for --validators

    ```bash
    docker run \
    -d \
    --restart always \
    --name eth-duties \
    tobiwo/eth-duties:latest \
    --validators 123456,456789 \
    --validators "111;My_Validator","222;Validator2" \
    --beacon-node http://localhost:5052
    ```

1. Print logs

    ```bash
    docker logs eth-duties --tail=20 -f
    ```

### Docker compose

You can find a template `compose.yaml` in the `docker` folder of this repository. Please replace all placeholders with actual values before using it. If you do not copy the compose to your own setup the commands for starting the container would be (from the root of this repo):

```bash
# Using compose plugin for docker
docker compose -f docker/compose.yaml up -d

# Using docker-compose binary
docker-compose -f docker/compose.yaml up -d
```

## Donate

If you like the tool and think this needs to be supported I highly appreciate any donations. Donations can be send in ETH, any ERC-20 or on Layer2 to the following address: `0x928Ae47264516F403Baf29871D8b43460F4f67aa`.

### Full disclosure

This project will be funded by the Ethereum Foundation with a small grant from the [ecosystem support program](https://esp.ethereum.foundation/applicants/small-grants=).
