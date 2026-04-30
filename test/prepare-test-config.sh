#!/bin/bash
# Populate dynamic fields in test/config.toml for a running kurtosis devnet.
#
# Fills:
#   [general]           working-beacon-node-url, rest-port-in-usage
#   [validators.active] in-sync-committee, next-sync-committee,
#                       not-in-sync-committee-not-proposing, proposing-blocks
#   [validator-nodes]   bearer-token, online-urls, expected-identifier-count,
#                       single-node-indices
#
# Also regenerates validator-nodes data files under ./test/data/ using the
# discovered token + URLs:
#     online-validator-nodes, online-validator-nodes-duplicates,
#     some-online-validator-nodes, online-and-wrong-auth-validator-nodes,
#     online-single-validator-node
#
# Usage:   ./test/prepare-test-config.sh   (run from repo root)
# Env:     ENCLAVE (default: eth-duties-devnet)
#          CONFIG_FILE (default: ./test/config.toml)
#          VALIDATOR_POOL_SIZE (default: 768)
#          PICK_COUNT (default: 4)

set -euo pipefail

ENCLAVE="${ENCLAVE:-eth-duties-devnet}"
CONFIG_FILE="${CONFIG_FILE:-./test/config.toml}"
VALIDATOR_POOL_SIZE="${VALIDATOR_POOL_SIZE:-768}"
PICK_COUNT="${PICK_COUNT:-4}"
PROPOSING_PICK_COUNT=3
DATA_DIR="./test/data"
KEYMANAGER_ARTIFACT="keymanager_file"
KEYMANAGER_FILE_NAME="keymanager.txt"
OFFLINE_SENTINEL_URLS=("http://127.0.0.1:34122" "http://127.0.0.1:34123")

for cmd in kurtosis curl jq awk sed mktemp; do
	if ! command -v "$cmd" >/dev/null 2>&1; then
		echo "Required command '$cmd' not found in PATH" >&2
		exit 1
	fi
done

if [[ ! -f "$CONFIG_FILE" ]]; then
	echo "config.toml not found at $CONFIG_FILE" >&2
	exit 1
fi

if [[ ! -d "$DATA_DIR" ]]; then
	echo "Data directory not found at $DATA_DIR" >&2
	exit 1
fi

echo "Inspecting kurtosis enclave '$ENCLAVE'..."
inspect=$(kurtosis enclave inspect "$ENCLAVE")

beacon_node=$(awk '
    $2 ~ /^cl-1-/ {
        for (i = 1; i <= NF; i++) {
            if ($i ~ /^http:\/\/127\.0\.0\.1:[0-9]+$/) {
                print $i
                exit
            }
        }
    }' <<<"$inspect")

port_in_usage=$(awk '
    $2 == "dora" {
        for (i = 1; i <= NF; i++) {
            if ($i ~ /^http:\/\/127\.0\.0\.1:[0-9]+$/) {
                split($i, a, ":")
                print a[3]
                exit
            }
        }
    }' <<<"$inspect")

if [[ -z "$beacon_node" ]]; then
	echo "Could not extract beacon node URL (cl-1-*) from kurtosis inspect output" >&2
	exit 1
fi
if [[ -z "$port_in_usage" ]]; then
	echo "Could not extract dora port from kurtosis inspect output" >&2
	exit 1
fi

echo "Beacon node:   $beacon_node"
echo "Port in usage: $port_in_usage (dora)"

current_slot=$(curl -sf "$beacon_node/eth/v1/beacon/headers/head" | jq -r '.data.header.message.slot')
current_epoch=$((current_slot / 32))
next_proposer_epoch=$((current_epoch + 1))
next_sync_epoch=$((current_epoch + 256))

echo "Current epoch: $current_epoch"

pool=$(jq -cn --argjson n "$VALIDATOR_POOL_SIZE" '[range(0; $n) | tostring]')

fetch_sync_indices() {
	local epoch="$1"
	curl -sf --location "$beacon_node/eth/v1/validator/duties/sync/$epoch" \
		--header 'Content-Type: application/json' \
		--data "$pool" |
		jq -c '[.data[].validator_index | tonumber]'
}

fetch_proposer_indices() {
	local epoch="$1"
	curl -sf --location "$beacon_node/eth/v1/validator/duties/proposer/$epoch" |
		jq -c '[.data[].validator_index | tonumber]'
}

current_sync=$(fetch_sync_indices "$current_epoch")
next_sync=$(fetch_sync_indices "$next_sync_epoch")
current_proposing=$(fetch_proposer_indices "$current_epoch")
next_proposing=$(fetch_proposer_indices "$next_proposer_epoch")

in_sync=$(jq -cn --argjson arr "$current_sync" --argjson k "$PICK_COUNT" \
	'$arr[:$k] | map(tostring)')
# Pick next-sync validators that are NOT in the current sync committee so the
# rest-endpoint response (deduplicated per validator) has 2 * PICK_COUNT entries.
next_sync_pick=$(jq -cn \
	--argjson cur "$current_sync" \
	--argjson nxt "$next_sync" \
	--argjson k "$PICK_COUNT" \
	'[$nxt[] | select(. as $x | $cur | index($x) | not)][:$k] | map(tostring)')

if (($(jq 'length' <<<"$next_sync_pick") < PICK_COUNT)); then
	echo "WARNING: next sync committee has fewer than $PICK_COUNT validators not in current." >&2
	echo "         Falling back to first $PICK_COUNT next-sync validators (overlaps with current)." >&2
	echo "         test_get_sync_committee_duties_from_rest_endpoint will fail until the devnet" >&2
	echo "         produces disjoint committees across periods. See docs/test.md." >&2
	next_sync_pick=$(jq -cn --argjson arr "$next_sync" --argjson k "$PICK_COUNT" \
		'$arr[:$k] | map(tostring)')
fi
proposing=$(jq -cn --argjson arr "$next_proposing" --argjson k "$PROPOSING_PICK_COUNT" \
	'$arr[-$k:] | map(tostring)')
not_in=$(jq -cn \
	--argjson cs "$current_sync" \
	--argjson ns "$next_sync" \
	--argjson cp "$current_proposing" \
	--argjson np "$next_proposing" \
	--argjson n "$VALIDATOR_POOL_SIZE" \
	--argjson k "$PICK_COUNT" \
	'($cs + $ns + $cp + $np) | unique as $used
     | [range(0; $n) | select(. as $i | $used | index($i) | not) | tostring][:$k]')

echo ""
echo "in-sync-committee:                    $in_sync"
echo "next-sync-committee:                  $next_sync_pick"
echo "not-in-sync-committee-not-proposing:  $not_in"
echo "proposing-blocks (last 3 of epoch+1): $proposing"
echo ""

update_array_field() {
	local key="$1"
	local array="$2"
	sed -i "s|^${key} = .*|${key} = ${array}|" "$CONFIG_FILE"
}

update_string_field() {
	local key="$1"
	local value="$2"
	sed -i "s|^${key} = .*|${key} = \"${value}\"|" "$CONFIG_FILE"
}

update_array_field "in-sync-committee" "$in_sync"
update_array_field "next-sync-committee" "$next_sync_pick"
update_array_field "not-in-sync-committee-not-proposing" "$not_in"
update_array_field "proposing-blocks" "$proposing"
update_string_field "rest-port-in-usage" "$port_in_usage"
update_string_field "working-beacon-node-url" "$beacon_node"

echo "Discovering validator keymanager endpoints..."

keymanager_tmp=$(mktemp -d)
trap 'rm -rf "$keymanager_tmp"' EXIT
if ! kurtosis files download "$ENCLAVE" "$KEYMANAGER_ARTIFACT" "$keymanager_tmp" \
	>/dev/null 2>&1; then
	echo "Could not download kurtosis artifact '$KEYMANAGER_ARTIFACT'" >&2
	exit 1
fi
if [[ ! -f "$keymanager_tmp/$KEYMANAGER_FILE_NAME" ]]; then
	echo "Expected '$KEYMANAGER_FILE_NAME' inside artifact '$KEYMANAGER_ARTIFACT'" >&2
	exit 1
fi
bearer_token=$(tr -d '\n\r\t ' <"$keymanager_tmp/$KEYMANAGER_FILE_NAME")
if [[ -z "$bearer_token" ]]; then
	echo "Bearer token from '$KEYMANAGER_FILE_NAME' is empty" >&2
	exit 1
fi

mapfile -t candidate_urls < <(awk '
    /http-validator:/ {
        for (i = 1; i <= NF; i++) {
            if ($i ~ /^http:\/\/127\.0\.0\.1:[0-9]+$/) {
                print $i
            }
        }
    }' <<<"$inspect")

if [[ ${#candidate_urls[@]} -eq 0 ]]; then
	echo "No http-validator endpoints found in kurtosis inspect output" >&2
	exit 1
fi

online_urls=()
online_keystore_counts=()
total_keystores=0
for url in "${candidate_urls[@]}"; do
	response=$(curl -sf --max-time 5 -H "Authorization: Bearer $bearer_token" \
		"$url/eth/v1/keystores" 2>/dev/null) || continue
	count=$(jq -r '.data | length' <<<"$response" 2>/dev/null || echo "")
	if [[ -z "$count" || "$count" == "null" ]]; then
		continue
	fi
	online_urls+=("$url")
	online_keystore_counts+=("$count")
	total_keystores=$((total_keystores + count))
	echo "  $url -> $count keystores"
done

if [[ ${#online_urls[@]} -eq 0 ]]; then
	echo "No validator keymanager endpoint accepted the shared bearer token" >&2
	exit 1
fi

online_urls_json=$(printf '%s\n' "${online_urls[@]}" |
	jq -cR . |
	jq -cs .)

update_array_field "online-urls" "$online_urls_json"
update_string_field "bearer-token" "$bearer_token"
sed -i "s|^expected-identifier-count = .*|expected-identifier-count = ${total_keystores}|" \
	"$CONFIG_FILE"

# Pick the VC with the fewest keystores to drive the standard-logging test
# against a known-small validator set. The test asserts that log counts match
# exactly, so the loaded validators must equal the tested ones.
single_vc_index=0
for i in "${!online_keystore_counts[@]}"; do
	if ((online_keystore_counts[i] < online_keystore_counts[single_vc_index])); then
		single_vc_index=$i
	fi
done
single_vc_url="${online_urls[$single_vc_index]}"
echo "Using $single_vc_url (${online_keystore_counts[$single_vc_index]} keystores) for single-VC test"

single_vc_pubkeys_json=$(curl -sf --max-time 10 \
	-H "Authorization: Bearer $bearer_token" \
	"${single_vc_url}/eth/v1/keystores" |
	jq -c '[.data[].validating_pubkey]')

if [[ -z "$single_vc_pubkeys_json" || "$single_vc_pubkeys_json" == "null" ]]; then
	echo "Could not fetch pubkeys from ${single_vc_url}" >&2
	exit 1
fi

single_vc_indices_request_body=$(jq -cn --argjson ids "$single_vc_pubkeys_json" '{ids: $ids}')
single_vc_indices_json=$(curl -sf --max-time 30 --location \
	--header 'Content-Type: application/json' \
	--data "$single_vc_indices_request_body" \
	"$beacon_node/eth/v1/beacon/states/head/validators" |
	jq -c '[.data[].index]')

if [[ -z "$single_vc_indices_json" || "$single_vc_indices_json" == "null" ]]; then
	echo "Could not resolve pubkeys to validator indices via $beacon_node" >&2
	exit 1
fi

single_node_indices_json=$(jq -c 'map(tostring)' <<<"$single_vc_indices_json")

if (($(jq 'length' <<<"$single_node_indices_json") == 0)); then
	echo "Smallest online VC has no keystores" >&2
	exit 1
fi

update_array_field "single-node-indices" "$single_node_indices_json"

echo ""
echo "Regenerating validator-nodes data files under $DATA_DIR..."

write_nodes_file() {
	local path="$1"
	shift
	: >"$path"
	for entry in "$@"; do
		printf '%s\n' "$entry" >>"$path"
	done
}

online_entries=()
for url in "${online_urls[@]}"; do
	online_entries+=("${url};${bearer_token}")
done

write_nodes_file "$DATA_DIR/online-validator-nodes" "${online_entries[@]}"

duplicates_entries=("${online_entries[0]}" "${online_entries[0]}")
if [[ ${#online_entries[@]} -ge 3 ]]; then
	duplicates_entries+=("${online_entries[2]}" "${online_entries[2]}")
else
	duplicates_entries+=("${online_entries[0]}" "${online_entries[0]}")
fi
write_nodes_file "$DATA_DIR/online-validator-nodes-duplicates" "${duplicates_entries[@]}"

some_online_entries=("${online_entries[0]}")
if [[ ${#online_entries[@]} -ge 2 ]]; then
	some_online_entries+=("${online_entries[1]}")
fi
for sentinel in "${OFFLINE_SENTINEL_URLS[@]}"; do
	some_online_entries+=("${sentinel};${bearer_token}")
done
write_nodes_file "$DATA_DIR/some-online-validator-nodes" "${some_online_entries[@]}"

# test_wrong_bearer_token_for_authentication expects VALIDATOR_NODE_AUTHORIZATION_FAILED_MESSAGE,
# which requires the remote to actually respond (401). Sentinel offline URLs would fail to
# connect instead — so pair a real online URL with a bogus token.
wrong_auth_entries=("${online_entries[0]}")
for ((i = 1; i < ${#online_urls[@]} && i < 3; i++)); do
	wrong_auth_entries+=("${online_urls[$i]};foobar")
done
write_nodes_file "$DATA_DIR/online-and-wrong-auth-validator-nodes" \
	"${wrong_auth_entries[@]}"

write_nodes_file "$DATA_DIR/online-single-validator-node" \
	"${online_entries[$single_vc_index]}"

echo ""
echo "bearer-token:              ${bearer_token:0:10}...${bearer_token: -6}"
echo "online-urls:               ${online_urls_json}"
echo "expected-identifier-count: ${total_keystores}"
echo "single-node-indices:       ${single_node_indices_json}"

echo ""
echo "Updated $CONFIG_FILE"
