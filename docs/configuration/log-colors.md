# Log colors

You can customize logging colors for all duty related logs with the following flags:

* `--log-color-warning`
    * affects duty logs where `--log_time_critical` < TIME_TO_DUTY <= `--log-time-warning`
    * affects sync committee duty logs when your validators will be in the next sync committee
* `--log-color-critical`
    * affects duty logs where TIME_TO_DUTY <= `--log-time-critical`
    * affects sync committee duty logs when your validators are in the current sync committee
* `--log-color-proposing`
    * affects proposing duty logs where TIME_TO_DUTY > `--log-time-warning`

You can use hex or rgb color codes for setting a respective color. The format needs to be:

* rgb: `255,255,255`
* hex: `#FFFFFF`

## Note on hex format

If you use hex format you need to wrap the hex code in `""` or `''` or separate the flag and the value with an `=`. This leads to the following possible formatting styles:

* `--log-time-warning=#FFFFFF`
* `--log-time-warning "#FFFFFF"`
* `--log-time-warning '#FFFFFF'`
