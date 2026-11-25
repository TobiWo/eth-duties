# Manual testing — PTC duties (EIP-7732 / Glamsterdam)

Manual verification steps for the payload timeliness committee (ptc) duty support added
for the Glamsterdam upgrade. These steps require a Gloas-enabled beacon node and must be
run on a machine which can start the Kurtosis devnet.

The automated integration tests (`test/run_tests.py`) skip all ptc cases when no validator
of the configured pool holds a ptc duty, which is always the case on a pre-Gloas devnet.
That makes these manual steps the real coverage for the feature.

## Prerequisites

```bash
conda activate poetry-py312
```

Start the devnet using the Glamsterdam spec already in the repo
(`test/ethereum-glamsterdam-devnet.yaml`, `gloas_fork_epoch: 1`, so ptc duties are live
from epoch 1), then populate the test config:

```bash
./test/start-kurtosis-devnet.sh    # or your usual kurtosis run with the glamsterdam spec
./test/prepare-test-config.sh
```

Export a beacon node URL from the enclave for the curl steps:

```bash
export BN=http://127.0.0.1:<cl-1-port>
```

---

## Step 1 — Validate the beacon API contract

**Do this first.** The whole implementation assumes a specific request/response shape, and
devnet client builds sometimes lag the spec.

```bash
curl -s "$BN/eth/v1/config/spec" | jq '.data.GLOAS_FORK_EPOCH'
# expect: "1"

curl -s -X POST "$BN/eth/v1/validator/duties/ptc/2" \
  -H 'Content-Type: application/json' -d '["0","1","2"]' | jq .
# expect: {dependent_root, execution_optimistic, data: [{pubkey, validator_index, slot}]}
```

`PtcDuty` mirrors the upstream JSON key names directly (no field mapping layer), so if
`data[]` entries carry extra or differently-named fields, `duties/fetcher/data_types.py`
needs adjusting.

An empty `data: []` only means those three indices are not in the ptc that epoch — retry
with more indices or a different epoch.

## Step 2 — Console output

Run eth-duties against the devnet with a validator set large enough to hit the ptc.

```bash
poetry run python duties/main.py \
  --validators <INDICES> \
  --beacon-nodes "$BN"
```

Expect lines of the form:

```text
Validator 123456 has next PTC duty in: 00:42 min. (slot: 9876543)
```

with the usual yellow/red coloring as the duty approaches.

| Symptom | Likely cause |
| --- | --- |
| Blank log lines | `SlotBasedDuty` wiring in `duties/fetcher/log.py` |
| Duty stuck at `00:00` | `set_time_to_duty` in `duties/protocol/ethereum.py` |

## Step 3 — Omit flag

```bash
poetry run python duties/main.py \
  --validators <INDICES> --beacon-nodes "$BN" --omit-ptc-duties
```

Expect: no ptc lines, `Logging ptc duties is omitted by the user` present, and
attestation / proposing / sync-committee lines unaffected.

## Step 4 — CICD regression (the important one)

Pick a validator which has a ptc duty but **no** attestation, proposing or sync-committee
duty, then:

```bash
poetry run python duties/main.py \
  --validators <PTC_ONLY_INDEX> --beacon-nodes "$BN" \
  --mode cicd-exit --omit-attestation-duties ; echo "exit=$?"
```

**Must print `exit=0`.**

An exit code of `1` means the ptc filter in `duties/helper/terminate.py`
(`__no_relevant_upcoming_duties`) is not working, and the tool would block CI pipelines
for a duty that is neither reward nor slashing relevant. Worth re-running across a few
epochs, since duty assignment shifts every epoch.

`test/test_helper/chain.py::get_validators_in_ptc_only` computes a suitable validator set
at runtime if you need one.

## Step 5 — REST endpoint

```bash
poetry run python duties/main.py \
  --validators <INDICES> --beacon-nodes "$BN" --rest &

curl -s localhost:5000/duties/raw/ptc | jq .     # expect the ptc duty list
curl -s localhost:5000/duties/any     | jq .     # expect {"any": true}
```

## Step 6 — Pre-Gloas regression

Point the same build at a beacon node from the **non-Gloas** `test/ethereum-devnet.yaml`
enclave.

Expect:

- the Gloas-inactive info message once at startup,
- no ptc log lines,
- **no repeated request retries** and no `Couldn't fetch any data from client` spam.

Fetching is gated by `ethereum.is_gloas_active()` before any HTTP call is made, so a
pre-Gloas node must never see a request to the ptc endpoint.

## Step 7 — Full suite

```bash
poetry run python test/run_tests.py
```

Against the Gloas devnet, the four ptc cases should run rather than skip:

- `test_logging_mode.test_omit_ptc_duties`
- `test_logging_mode.test_ptc_duty_logging`
- `test_cicd_mode.test_cicd_exit_mode_with_ptc_duties_only`
- `test_rest_api.test_get_ptc_duties_from_rest_endpoint`

To isolate a single case, use the `poetry run python -c ...` recipe from `docs/test.md`
and set `[test] debug = true` in `test/config.toml` for raw subprocess logs.

Public-network runs can produce false negatives, as proposer and sync-committee
assignments change and node load affects timing.

---

## Regression check for the fetcher refactor

`duties/fetcher/fetch.py` was refactored so all four duty types share one
`__fetch_duty_responses`, driven by the `DUTY_REQUEST_PROPERTIES` table. Behaviour is
unchanged, so **step 2 covers it**: attestation, sync-committee, proposing *and* ptc duties
must all still appear in the console.

A regression would surface as one duty type silently missing from the output.

Note: the previous `case _: return []` fallback is gone. An unmapped duty type now raises
`KeyError` instead of silently returning an empty list — a louder and more debuggable
failure.

## What can be checked without a devnet

```bash
poetry run mypy duties/     # expect ONLY the pre-existing duties/cli/arguments.py error
poetry run pylint duties/   # 10.00/10
poetry run black --check duties/ && poetry run isort --check duties/ test/
poetry run pydoclint --style=google duties/
pre-commit run --config .pre-commit/.pre-commit-config.yaml --all-files
poetry run python duties/main.py --help | grep omit-ptc
```

`mypy` is not wired into CI and is not clean at baseline — `duties/cli/arguments.py`
reports one pre-existing `int`/`None` error. Do not treat that as newly introduced.
