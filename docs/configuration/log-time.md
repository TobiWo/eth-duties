# Log time

The flag `--log-time-warning` is used as a threshold to color warning logs in a specified color. However, it is also used to log the proportion of all duties which will be executed after `--log-time-warning`. The log includes sync-committee and proposing duties and therefore is different from [--mode-cicd-attestation-time](./mode.md/#mode-cicd-attestation-time-and-mode-cicd-attestation-proportion) which is specific for the cicd modes. The idea is to get some general info on the number of upcoming duties.

## Example

* validator1 is in current sync committee (next sync committe starts in 3h)
* validator2 is in next sync committee (next sync committe starts in 3h)
* validator1 has attestation duty in 02:41 min.
* validator4 has attestation duty in 03:11 min.
* validator4 has proposing duty in 03:33 min.
* validator2 has attestation duty in 04:41 min.
* validator3 has attestation duty in 04:45 min.

```bash
# Assumed setting:
./eth-duties --log-time-warning 180 ...
# The log would be
71.43% of all duties will be executed in 180.0 sec. or later
```

```bash
# Assumed setting:
./eth-duties --log-time-warning 300 ...
# The log would be
14.29% of all duties will be executed in 300.0 sec. or later
# In this case only the next committee duty will be executed in 300 secs or later
```
