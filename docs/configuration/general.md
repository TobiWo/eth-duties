# Configuration

Most of the available flags are self explanatory. However, some may not be that obvious. Those flags are described in the respective subchapter.

For all available cli flags please call `eth-duties --help` or check the table below. See usage examples for further details.

## Available CLI flags

| flag | description | extended description |
| --- | --- | --- |
| `-h` / `--help` | Show all available cli flags | :no_entry: |
| `--beacon-nodes` | Comma separated list of URLs to access the beacon node api (default: <http://localhost:5052>) | [link](./beacon-nodes.md) |
| `--interval` | Interval in seconds for fetching data from the beacon node (default: 15) | :no_entry: |
| `--log` | Defines log level. Values are 'DEBUG' or 'INFO' (default: 'INFO') | :no_entry: |
| `--log-pubkeys` | If supplied the validator index will be replaced with the pubkey in log messages | :no_entry: |
| `--log-color-warning` | The logging color as hex or rgb code for warning logs (default: '255,255,0' - yellow) | [link](./log-colors.md) |
| `--log-color-critical` | The logging color as hex or rgb code for critical logs (default: '255, 0, 0' - red) | [link](./log-colors.md) |
| `--log-color-proposing` | The logging color as hex or rgb code for proposing duty logs (default: '0, 128, 0' - green) | [link](./log-colors.md) |
| `--log-time-warning` | The threshold at which a time to duty warning log (in seconds) will be colored in YELLOW (default: 120) | :no_entry: |
| `--log-time-critical` | The threshold at which a time to duty critical log (in seconds) will be colored in RED (default: 60) | :no_entry: |
| `--max-attestation-duty-logs` | The max. number of validators for which attestation duties will be logged (default: 50) | :no_entry: |
| `--mode` | The mode which eth-duties will run with. Values are 'log', 'no-log', 'cicd-exit', 'cicd-wait' or 'cicd-force-graceful-exit' (default: 'log') | [link](./mode.md) |
| `--mode-cicd-waiting-time` | The max. waiting time until eth-duties exits in cicd-wait mode (default 780 sec. (approx. 2 epochs)) | [link](./mode.md/#cicd-wait) |
| `--mode-cicd-attestation-time` | If a defined proportion of attestion duties is above the defined time threshold the application exits gracefully in any cicd-mode (default 240 sec.) | [link](./mode.md/#mode-cicd-attestation-time-and-mode-cicd-attestation-proportion) |
| `--mode-cicd-attestation-proportion` | The proportion of attestation duties which needs to be above a defined time threshold to force the application to exit gracefully (default 1) | [link](./mode.md/#mode-cicd-attestation-time-and-mode-cicd-attestation-proportion) |
| `--omit-attestation-duties` | If supplied upcoming attestation duties will not be logged to the console | :no_entry: |
| `--rest` | Starts a rest server on port 5000 | [link](./restful-api.md) |
| `--rest-host` | Host from which requests will be accepted (default 0.0.0.0) | [link](./restful-api.md) |
| `--rest-port` | Port where the rest server is exposed (default 5000) | [link](./restful-api.md) |
| `--validators` | One or many validator identifiers for which next duties will be fetched (argument can be provided multiple times) | [link](./validator-identifiers.md) |
| `--validators-file` | File with validator identifiers where every identifier is on a separate line | [link](./validator-identifiers.md/#validators-file) |
