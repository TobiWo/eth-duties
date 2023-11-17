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
