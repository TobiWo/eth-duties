# Testing

Currently, there are no unit tests available for eth-duties. This is mainly because testing Python CLI applications is difficult. Additionally, it would be simpler to conduct tests if eth-duties utilized `clique` instead of `argparse` as its CLI parser, as `pytest`, a prominent Python testing framework, offers specific test functions for `clique`. However, switching to `clique` would require completely redesigning the application, which isn't practical at the moment.

Given these constraints, I've opted to develop integration tests instead. Fortunately, eth-duties primarily logs its findings to the console, allowing for the testing of most functionalities by monitoring these logs. I've created a simple test framework for this purpose. The approximate workflow is as follows:

1. Start eth-duties in the background
1. Scan the logs
1. Stop the process on specific trigger log
1. Compare fetched logs with expected logs

## Configure

There is a `config.toml` availabe in the test folder. The already present values will work for a beacon node connected to the Holesky testnet. If you have a private network or connect to a different public network adapt the values accordingly. **Note: Values for validators which are in the sync committee or are about to propose a block are not provided as their status keeps changing constantly**

## Run tests

You need to install all dependencies and setup the project by following the [contribution guideline](contribute.md/#installation). Once that is finished and the `config.toml` is populated you can start the test suite with:

```bash
poetry run python test/run_tests.py
```

## Known issues

Since all tests rely on the connection to a beacon node and therefore a real world network you can't predict the outcome to 100%. This is especially true when your beacon node is under heavy load already. You need to consider that when you see failing tests. This does not necessarily mean that a specific functionality is broken.

There are two ways to check if a test really failed:

1. Repeat the test on it's own by commenting out all other tests in `test/run_tests.py`
1. Activate debugging (print fetched logs to the console) while set the debug setting in `config.toml` to true
    - with debugging active you can check the expected logs (see `cases` folder) and compare them with the actual logs

## Improvements

The best way to improve reliability for the present tests would be to spin up a private network and use this for testing. This could be realized e.g. with a full comprehensive compose. If anyone wants to help I'm happy to work with you :smiley:.
