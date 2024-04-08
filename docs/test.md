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
1. Update client image tags in `./test/ethereum-devnet.yaml` if outdated
1. Fire up the devnet from the root of the `eth-duties` repository with:

    ```bash
    kurtosis run --enclave eth-duties-devnet github.com/kurtosis-tech/ethereum-package --args-file ./test/ethereum-devnet.yaml
    ```

## Configure tests

There is a `config.toml` availabe in the test folder. The already present values will work for the aforementioned local devnet created with `kurtosis cli`. If you want to run the tests against a public network adapt the values accordingly. **Note: Values for validators which are in the sync committee or are about to propose a block are not provided as their status keeps changing constantly, even on the local devnet.**

### Get specific validators for config

In order to run the test suite you need to populate the `config.toml` properties. It is a bit complex to get correct values for the following properties:

- in-sync-committee
- next-sync-committee
- not-in-sync-committee-not-proposing
- proposing-blocks

In the following chapters I describe how to get these values for a local devnet. You need to send some REST calls to your beacon node like `eth-duties` does it as well. Additionally, some calls refer to `CONTENT_OF_CURL_TEST_DATA_FILE` which is located here: `test/data/curl-test-data`. Just copy the content and paste it into the quotes of the respective data flag. If you run the test suite against a real world network you need to adapt the test data.

You need to retrieve the current epoch for all of the below calls. The easiest way to get the current epoch of your local devnet is to use dora, a simple beachon chain explorer. To get the port were dora is exposed to just run:

```bash
kurtosis enclave inspect eth-duties-devnet
```

#### Validators in current sync committee

1. Get the current epoch for your local devnet via dora
1. Send `POST` call:

    ```bash
    curl --location 'http://127.0.0.1:<BEACON_NODE_API_PORT>/eth/v1/validator/duties/sync/<CURRENT_EPOCH>' \
    --header 'Content-Type: application/json' \
    --data 'CONTENT_OF_CURL_TEST_DATA_FILE'
    ```

1. Extract as many validator indices as you like and add to `config.toml`

#### Validators in next sync committee

If you just started a fresh local devnet the values can be the same as [above](#validators-in-current-sync-committee). The background is that validators will be the same at least for the first two sync committee periods. It is unclear at which point different indices are chosen as these are protocol genesis specifics which are out of my knowledge.

If you keep your devnet running for a longer time the procedure would be the following:

1. Get the current epoch via e.g. beaconcha.in for public networks or dora for your local devnet
1. Send `POST` call:

    ```bash
    curl --location 'http://127.0.0.1:<BEACON_NODE_API_PORT>/eth/v1/validator/duties/sync/<CURRENT_EPOCH+256>' \
    --header 'Content-Type: application/json' \
    --data 'CONTENT_OF_CURL_TEST_DATA_FILE'
    ```

1. Extract as many validator indices as you like and add to `config.toml`

#### Validators not in any sync committee and not proposing blocks

1. Just use the output of the aforementioned calls and find validator indices which are neither in the current nor in the next sync committee
1. Get the current epoch via e.g. beaconcha.in for public networks or dora for your local devnet
1. Send `GET` calls:

    ```bash
    curl --location 'http://127.0.0.1:<BEACON_NODE_API_PORT>/eth/v1/validator/duties/proposer/<CURRENT_EPOCH>'
    curl --location 'http://127.0.0.1:<BEACON_NODE_API_PORT>/eth/v1/validator/duties/proposer/<CURRENT_EPOCH+1>'
    ```

1. Find indices which are not in any sync committee and will not propose a block in the current and upcoming epoch
1. Extract as many validator indices as you like and add to `config.toml`

#### Validators which will propose a block

1. Get the current epoch via e.g. beaconcha.in for public networks or dora for your local devnet
1. Send `GET` call:

    ```bash
    curl --location 'http://127.0.0.1:<BEACON_NODE_API_PORT>/eth/v1/validator/duties/proposer/<CURRENT_EPOCH+1>'
    ```

1. Extract as many validator indices as you like and add to `config.toml`
    - I recommend to extract validator indices from the end of the returned list as these are the ones which will propose a block in the most distant future (running the suite may take some time so it is a good idea to have a time buffer)

## Run tests

You need to install all dependencies and setup the project by following the [contribution guideline](contribute.md/#installation). Once that is finished and the `config.toml` is populated you can start the test suite with:

```bash
poetry run python test/run_tests.py
```

## Known issues

### False negatives

If you connect to a real world network like Holesky you can't predict the outcome to 100%. This is especially true when your beacon node is under heavy load already. You need to consider that when you see failing tests. This does not necessarily mean that a specific functionality is broken.

There are three ways to check if a test really failed:

1. Repeat the test on it's own by commenting out all other tests in `test/run_tests.py`
1. Activate debugging (print fetched logs to the console) while set the debug setting in `config.toml` to true
    - with debugging active you can check the expected logs (see `cases` folder) and compare them with the actual logs
1. Run test suite against a local devnet

### Bugs

The test suite already revealed a [bug](https://github.com/TobiWo/eth-duties/issues/78) which results in one failing test (test: test_get_sync_committee_duties_from_rest_endpoint) if you run the suite against a local devnet which is running for less than 24h. Find more details via the link above.
