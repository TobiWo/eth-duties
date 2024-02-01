from argparse import Namespace

MOCK_STANDARD_ARGUMENTS = Namespace(
    beacon_nodes=["http://localhost:5052"],
    interval=15,
    log="INFO",
    log_pubkeys=False,
    log_color_warning=[255, 255, 0],
    log_color_critical=[255, 0, 0],
    log_color_proposing=[0, 128, 0],
    log_time_warning=120.0,
    log_time_critical=60.0,
    max_attestation_duty_logs=50,
    mode="log",
    mode_cicd_waiting_time=780,
    mode_cicd_attestation_time=240,
    mode_cicd_attestation_proportion=1,
    omit_attestation_duties=False,
    rest=False,
    rest_host="0.0.0.0",
    rest_port=5000,
    validators=[["123"]],
    validators_file=None,
)
