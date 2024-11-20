# Validator identifiers

## Accepted formats

The following formats are accepted:

* validator index e.g. 123456
* validator pubkey e.g. 0xaffc434cf8138634a4cd0ef6cb815febd3db25760b1b6c522f9b4aa78e599b60336d7dd2e953192e45d4ac91f66f0723
* validator index/pubkey with alias e.g. "123456;my-validator"

## Separation

The following separation rules apply while adding multiple identifiers.

* Validator identifiers can be separated by comma or space e.g.:
    * `--validators 123 456 --validators 678 999`
    * `--validators 123,456 --validators 678,999`
* If you provide a validator identifier with an alias you need to wrap the whole string of one identifier-alias-pair in quotes or double quotes e.g.:
    * `--validators "123;val1" "456;val2" --validators 678 999` or
    * `--validators '123;val1','456;val2' --validators 678,999`

**Note: Wrapping an identifier-alias-pair in additional quotes or double quotes (beside the necessary double quotes for yaml) is not true for a `docker-compose`. Please check the example compose files provided in the docker folder.**

## Validators file

File where each validator identifier is saved on a separate line. Formats are accepted as described [above](#accepted-formats).

Example:

```text
15105
251427 ; GO_FOR_IT
234;My_Validator
0x99f094ff7dc4b521a5075fa03ca1fe468546dfe053124d88187cce6de3332c7d65e4b0738cd85e037d7cbbc48c6645eb
```

## Validator nodes

Path to a file containing connection information (`URL;BEARER`) for validator nodes to fetch the validator identifiers (pubkeys) managed by the respective node. The data is retrieved via the [keymanager api](https://ethereum.github.io/keymanager-APIs/) from the respective node. This approach eliminates the need to manually provide validator identifiers using `--validators` or `--validators-file`. Additionally, the managed validator identifiers and their status are updated regularly. By default, updates occur once per day, but this can be adjusted using the `--validator-update-interval` setting. This feature is particularly beneficial for professional node operators managing a large and fluctuating number of validators.

Note, you can supply additional validators via one of the other two cli flags (`--validators`, `--validators-file`).

### Supported clients / remote signer

Not all clients support the keymanager api yet. Furthermore, I did not had the time yet to test all clients/remote signers.

| client | tested | compatible |
|  --- |  --- | --- |
| prysm | :white_check_mark: | :exclamation: |
| lighthouse | :white_check_mark: | :white_check_mark: |
| teku | :white_check_mark: | :white_check_mark: |
| nimbus | :white_check_mark: | :white_check_mark: |
| lodestar | :white_check_mark: | :white_check_mark: |
| grandine | :white_check_mark: | :x: |
| vouch | :x: | :x: |
| web3signer | :x: | :white_check_mark: |
| dirk | :x: | :x: |

#### Notes

1. There are some issues with prysm currently. More specifically, if you use prysm but validators are managed by a remote signer, eth-duties will not work since the respective endpoint is broken. If validators are managed locally everything works as expected. **This issue will be fixed in version `v5.1.3`**.

### File structure

The validator nodes file needs to be structured like this:

```text
http://localhost:5062;234ddgret353f23r
http://192.168.0.1:5062;34547342erg45g57
https://my-awesome-validator-node;234723022hnfn
```

### Keymanager API

The keymanager API is not enabled by default, and the quality of documentation varies across different clients. Below is a list of documentation chapters that explain how to enable the API for each client/remote signer:

* [lighthouse](https://lighthouse-book.sigmaprime.io/api-vc.html)
* [teku](https://docs.teku.consensys.io/how-to/use-external-signer/manage-keys#enable-validator-client-api)
* [nimbus](https://nimbus.guide/keymanager-api.html)
* [lodestar](https://chainsafe.github.io/lodestar/contribution/dev-cli#--keymanager)
* [prysm](https://docs.prylabs.network/docs/how-prysm-works/keymanager-api)
* [web3signer](https://docs.web3signer.consensys.io/how-to/manage-keys#manage-keys-using-key-manager-api)

Note: **Ensure you fully understand the process before activating the API. Accidentally exposing endpoints to the public can allow external parties to exit or delete your validators. Eth-duties only accesses three getter endpoints of the [keymanager api](https://ethereum.github.io/keymanager-APIs/). To verify that Eth-Duties cannot delete any of your keys or exit your validators, you can search for the corresponding modifier endpoints in the GitHub repository.**

### Caveat

1. If `eth-duties` attempts to update the validator identifiers from the provided list of validator nodes and one or more nodes are not accessible, it will delete all identifiers for those nodes internally until they become reachable again. I have an idea for optimizing this behavior to retain the previous state of validator identifiers when a node is unavailable. However, implementing this improvement will require some code refactoring and, consequently, time.
1. If all validator nodes are unreachable, eth-duties will enter a dead state and will remain in this state even if the nodes come back online. The aforementioned optimization will address this issue as well. To avoid the dead state currently, you need to provide one or more validators via `--validators`.
1. Currently, you cannot supply aliases with --validator-nodes. This might change in future updates.
