<!-- markdownlint-disable MD033 -->

# eth-duties

ETH-duties logs upcoming validator duties to the console in order to find the best maintenance period for your validator(s). In general the tool was developed to mainly help home validators but it still can be used on a larger scale (see [usage](#usage) examples).

## Caveat

1. The tool does not check for sync committee duties currently. This is the feature with the highest priority and will be implemented soon.
1. Currently the tool can only handle validator indices but I will add pubkey handling as well (see [todo](#todos) list).
1. I only tested the tool with the following beaon clients:

    * lighthouse
    * teku

   However, since it only calls official ETH2 spec endpoints it should work with every client. As a side node, I had issues with `Teku 22.10.1` as the tool crashed from time to time. I read in the teku release notes that they updated their REST API framework in version `22.10.2` and since then I did not experience any issues.

**Please use the tool at your own risk. Since it is very early I probably would connect it to a beacon client which is not connected to a validator.**

## What to expect

Beside the actual functionality of logging upcoming duties I added some kind of UX in form of color coding.

The color coding comprises of:

| Color | Description |
| --- | --- |
| GREEN | Indicates upcoming block proposer duties |
| YELLOW | The upcoming duty will be performed in less than 2 minutes **or** your validator was chosen to be part in the next sync committee |
| RED | The upcoming duty will be performed in less than 1 minute **or** your validator is partof the current sync committee |

Note: **Sync committee duties are not implemented yet (see [caveat](#caveat))**

### Examples

1. Attestion duties for some validators ![attestations](./img/attestations.PNG)
1. Block proposing duties for some validators ![proposing](./img/proposing.PNG)

## Requirements

* `Python 3.10`

The tool explicitly needs `Python 3.10` as I use a feature which was just introduced with this version. If it turns out that this is a major hurdle I can replace that part of the code with some other logic.

`Python 3.11` will not work currently as the dependencies weren't updated for that version yet.

In general it is recommended to work with virtual environments instead of a global python installation. This is out of scope of this documentation.

## Installation

I will add full dependency management and also a binary release in the future. For now you need to call the python binary to execute the program. Therefore you need to perform some steps before usage.

### Anaconda

The following workflow is based on [miniconda/Anaconda](https://docs.conda.io/en/latest/miniconda.html). Make sure you can call the conda binary/executable in your terminal.

1. Navigate to the root folder of the repository
1. Execute
  
    ```bash
    conda env create -f development_env.yaml
    ```

1. Activate your newly created conda environment

    ```bash
    conda activate eth-duties
    ```

### Pip

I also added a requirements.txt to install the dependencies with pip.

1. Navigate to the root folder of the repository
1. Execute
  
    ```bash
    pip install -r requirements.txt
    ```

## Usage

As for the installation, please navigate to the projects root folder.

1. Print the help:

    ```bash
    python duties/duties.py --help
    ```

1. Print upcoming duties for two validators while connecting to a local beacon client:

    ```bash
    python duties/duties.py --validators <VALIDATOR_INDEX_1> <VALIDATOR_INDEX_2> --beacon-node http://localhost:5052
    ```

1. Print upcoming duties for validators which indices are located in a file:

    ```bash
      python duties/duties.py --validator-file <PATH_TO_VALIDATOR_FILE> --beacon-node http://localhost:5052
    ```

1. Print upcoming validator duties but omit attestation duties specifically. This can be useful for professional node operators or individuals with a lot of validators as printing upcoming attestation duties for a lot of validators might get messy and you want to concentrate on the important stuff:

    ```bash
    python duties/duties.py --validator-file <PATH_TO_VALIDATOR_FILE> --beacon-node http://localhost:5052 --omit-attestation-duties
    ```

## Run in Docker

1. Build image

    ```bash
    docker build -t tobiwo/eth-duties:latest -f docker/dockerfile .
    ```

1. Run container

    ```bash
    docker run --rm --name eth-duties tobiwo/eth-duties:latest -v "123456, 456789" -b "http://locahost:5052"
    ```

1. Run container on boot

    ```bash
    docker run -d --restart always --name eth-duties tobiwo/eth-duties:latest -v "123456, 456789" -b "http://locahost:5052"
    ```

1. Print logs

    ```bash
    docker logs eth-duties --tail=20 -f
    ```

## ToDos

* fetch and process sync committee duties
* add validator pubkey parsing
* add space trimming to index and pubkey parsing from file
* add some explainer at program start for color coding
* improve fetching in case no duties could be detected
  * only fetch if new epoch started
* implement asyncio to improve UX and optimize fetching logic
* test with nimbus and lodestar
