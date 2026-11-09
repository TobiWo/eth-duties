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
    conda activate poetry-py312
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

## Update dependencies

`poetry install` only installs the versions from `poetry.lock`. To update dependencies, update the lock file first.

Direct dependencies in `pyproject.toml` use caret constraints (e.g. `^6.0.0` allows `>=6.0.0,<7.0.0`; `^0.162.0` allows `>=0.162.0,<0.163.0`). The exact versions are pinned in `poetry.lock`.

1. Update all dependencies within their constraints

    ```bash
    # Updates poetry.lock (incl. transitive dependencies) and installs the new versions
    poetry update
    ```

1. List remaining outdated dependencies

    ```bash
    # Only direct dependencies; these need a new major version (or a new minor version for 0.x versions)
    poetry show --outdated --top-level
    ```

1. Upgrade remaining outdated direct dependencies deliberately and check for breaking changes

    ```bash
    # Updates the constraint in pyproject.toml, poetry.lock and installs the new version
    poetry add <PACKAGE>@^<VERSION>

    # For dev dependencies
    poetry add --group dev <PACKAGE>@^<VERSION>
    ```

## Code quality

Please run the following formatter and linter and fix respective issues in order to keep code quality high. You can also install IDE integrations if available.

```bash
# From the root of the repository
poetry run black duties/
poetry run pylint duties/
poetry run pydoclint --style=google duties/
```
