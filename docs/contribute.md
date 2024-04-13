# Contribute

If you want to contribute you need to setup the project which is described in this section.

## Requirements

* `Python 3.12 or higher`
* in general it is recommended to work with virtual environments instead of a global python installation. This is out of scope of this documentation.

## Installation

Dependencies are organized and managed using poetry. Poetry itself needs `Python 3.8` or later.

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
