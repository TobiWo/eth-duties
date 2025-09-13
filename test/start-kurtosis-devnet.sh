#!/bin/bash

while IFS='=' read -r key value; do
	if [[ "$key" =~ ^# ]] || [[ -z "$key" ]]; then
		continue
	fi
	export "$key"="$value"
	exported_vars+=("$key")
done <./ethereum-devnet-tags.env

envsubst <./ethereum-devnet-small.yaml >./ethereum-devnet-small-replace.yaml
kurtosis run --image-download always --enclave eth-duties-devnet github.com/ethpandaops/ethereum-package --args-file ./ethereum-devnet-small-replace.yaml &&
	rm ./ethereum-devnet-small-replace.yaml &&
	for var in "${exported_vars[@]}"; do
		unset "$var"
	done
