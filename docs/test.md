# Testing

Currently, there are no unit tests available for eth-duties. This is mainly because testing Python CLI applications is difficult. Additionally, it would be simpler to conduct tests if eth-duties utilized `clique` instead of `argparse` as its CLI parser, as `pytest`, a prominent Python testing framework, offers specific test functions for `clique`. However, switching to `clique` would require completely redesigning the application, which isn't practical at the moment.

Given these constraints, I've opted to develop integration tests instead. Fortunately, eth-duties primarily logs its findings to the console, allowing for the testing of most functionalities by monitoring these logs. I've created a simple test framework for this purpose. The approximate workflow is as follows:

1. Start eth-duties in the background
1. Scan the logs
1. Stop the process on specific trigger log
1. Compare fetched logs with expected logs

## Local devnet

You can run the integration test suite against any real world Ethereum network (mainnet, Holesky etc.). However, since the increased undeterministic properties of these networks, tests might fail which normally wouldn't fail. Therefore I added a config yaml for the `ethereum-package` for `kurtosis cli` with which you can easily start an own local devnet which is much more predictable in terms of network properties.

### Setup

1. [Install kurtosis cli](https://docs.kurtosis.com/install/)
1. Update client image tags in `./test/ethereum-devnet-tags.env` if outdated
1. Fire up the devnet from the root of the `eth-duties` repository and cleanup env variables as well as repo from temp config file:
    - Note: The command may or may not work on gitbash for Windows but it is only tested on Linux (Ubuntu)

    ```bash
    export $(grep -v '^#' ./test/ethereum-devnet-tags.env | xargs) && \
    cat ./test/ethereum-devnet.yaml | envsubst > ./test/ethereum-devnet-replace.yaml && \
    kurtosis run --image-download always --enclave eth-duties-devnet github.com/ethpandaops/ethereum-package --args-file ./test/ethereum-devnet-replace.yaml && \
    rm ./test/ethereum-devnet-replace.yaml && \
    unset $(grep -v '^#' ./test/ethereum-devnet-tags.env | sed -E 's/(.*)=.*/\1/' | xargs)
    ```

## Configure tests

There is a `config.toml` available in the test folder. The already present values will work for the aforementioned local devnet created with `kurtosis cli`. If you want to run the tests against a public network, adapt the values accordingly.

The following fields change between devnet runs (or, in the case of sync-committee / proposer assignments, constantly) and therefore ship empty in `config.toml`:

- `[general]` `working-beacon-node-url`, `rest-port-in-usage`
- `[validators.active]` `in-sync-committee`, `next-sync-committee`, `not-in-sync-committee-not-proposing`, `proposing-blocks`
- `[validator-nodes]` `bearer-token`, `online-urls`, `expected-identifier-count`, `single-node-indices`

### Populate dynamic config fields

Run the helper script against a running kurtosis devnet:

```bash
./test/prepare-test-config.sh
```

The script:

1. Reads `kurtosis enclave inspect eth-duties-devnet` to extract the `cl-1-*` beacon node URL and the `dora` port.
1. Queries the beacon node for the current epoch, current + next sync committees, and current + next epoch proposer duties.
1. Picks 4 validator indices for each sync-related field and the last 3 indices of the next-epoch proposer list for `proposing-blocks` (trailing entries give the running test suite enough head room before those slots arrive). `next-sync-committee` is chosen disjoint from `in-sync-committee` so the REST sync-committee test sees distinct per-validator entries for both committees.
1. Downloads the `keymanager_file` kurtosis artifact to read the shared bearer token and probes every `http-validator` endpoint with it. Endpoints that accept the token are recorded under `[validator-nodes] online-urls`; their total keystore count is stored as `expected-identifier-count`.
1. Resolves the keystores of the smallest online VC to their validator indices (POST `/eth/v1/beacon/states/head/validators`) and writes them to `single-node-indices`. The same VC is pointed to by `online-single-validator-node`, so the standard-logging-mode test for `--validator-nodes` can match loaded vs. tested validators exactly.
1. Regenerates the validator-nodes data files under `./test/data/` (`online-validator-nodes`, `online-validator-nodes-duplicates`, `some-online-validator-nodes`, `online-and-wrong-auth-validator-nodes`, `online-single-validator-node`) using the discovered URLs and token. These files are gitignored because they embed devnet-specific secrets.
1. Writes all fields back into `./test/config.toml` in place.

Environment overrides:

- `ENCLAVE` (default `eth-duties-devnet`)
- `CONFIG_FILE` (default `./test/config.toml`)
- `VALIDATOR_POOL_SIZE` (default `768`)
- `PICK_COUNT` (default `4`)

For public networks the script will not work as-is. Populate the fields manually by hitting the equivalent `/eth/v1/validator/duties/{sync,proposer}/<epoch>` endpoints against your node, and supply keymanager bearer tokens from your own validator clients.

## Run tests

You need to install all dependencies and setup the project by following the [contribution guideline](contribute.md/#installation). Once that is finished and the `config.toml` is populated you can start the test suite with:

```bash
poetry run python test/run_tests.py
```

### Run a single test in isolation

Helpful when you just added a new test case or want to debug a specific failure without running the full suite (~3 minutes). Each test function in `test/cases/*.py` returns `1` on success and `0` on failure, so it can be invoked directly:

```bash
poetry run python -c "
import sys
sys.path.insert(0, 'test')
sys.path.insert(0, 'duties')
from cases import test_logging_mode
result = test_logging_mode.test_omit_sync_committee_duties()
print('RESULT:', result)
"
```

Replace `test_logging_mode` and `test_omit_sync_committee_duties` with the module and function you want to run. Enable `[test] debug = true` in `test/config.toml` to also print the raw subprocess logs, which helps when verifying that the expected log strings actually appear.

## Known issues

### False negatives

If you connect to a real world network like Hoodi you can't predict the outcome to 100%. This is especially true when your beacon node is under heavy load already. You need to consider that when you see failing tests. This does not necessarily mean that a specific functionality is broken.

There are three ways to check if a test really failed:

1. Repeat the test on it's own by commenting out all other tests in `test/run_tests.py`
1. Activate debugging (print fetched logs to the console) while set the debug setting in `config.toml` to true
    - with debugging active you can check the expected logs (see `cases` folder) and compare them with the actual logs
1. Run test suite against a local devnet

### Bugs

The test suite already revealed a [bug](https://github.com/TobiWo/eth-duties/issues/78) which results in one failing test (test: test_get_sync_committee_duties_from_rest_endpoint) if you run the suite against a local devnet which is running for less than 24h. Find more details via the link above.
