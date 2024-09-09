# Add validators to local kurtosis devnet

1. Start kurtosis devnet with the following global parameters:

    ```bash
    keymanager_enabled: true
    port_publisher:
      el:
        enabled: true
      cl:
        enabled: true
      vc:
        enabled: true
      additional_services:
        enabled: true
      network_params:
        eth1_follow_distance: 1
    ```

1. Get node information with `kurtosis enclave inspect <ENCLAVE_NAME/UUID>`

1. Set node connection env variables:

    ```bash
    export BEACON_NODE=<BEACON_NODE_URL>
    export VALIDATOR_NODE=<VALIDATOR_NODE_URL>
    export EXECUTION_NODE=<EXECUTION_NODE_URL>
    ```

1. Get devnet genesis data

    ```bash
    # You need fork version for creating genesis data
    curl --location "${BEACON_NODE}/eth/v1/beacon/genesis"
    ```

1. Start [eth2-val-tools](https://github.com/protolambda/eth2-val-tools/tree/master) docker container:

    ```yaml
    # compose.yaml
    ---
    name: "eth2-val-tools"

    services:

      eth2-val-tools:
        container_name: "eth2-val-tools"
        image: "protolambda/eth2-val-tools:latest"
        entrypoint: "/bin/sh"
        tty: true
        volumes:
          - "./output:/app/output/"
        networks:
          - "val-tools"

    networks:
      val-tools:
        name: "val-tools"
    ...
    ```

    * Store the above compose to `compose.yaml` and start container with:

      ```bash
      docker compose up -d
      ```

1. Exec into eth2-val-tools docker container:

    ```bash
    docker exec -it eth2-val-tools bash
    ```

1. Create keystores and deposit-data:

    ```bash
    # Create mnemonic
    ./eth2-val-tools mnemonic
    
    # Create keystores
    ./eth2-val-tools keystores --source-min 0 --source-max 2  --source-mnemonic "YOUR_MNEMONIC"

    # Create deposit-data
    ./eth2-val-tools deposit-data --fork-version "<FORK_VERSION_FROM_GENESIS_DATA>" --source-min 0 --source-max 2 --validators-mnemonic "YOUR_MNEMONIC" --withdrawals-mnemonic "YOUR_MNEMONIC" > ./assigned_data/deposit-data.json
    
    # Copy everything to output folder
    cp -r assigned_data/* ./output/

    # Leave container after you copied everything to ./output
    ```

1. Copy files from mounted folder and change owner

    ```bash
    mkdir data
    cp -r ./output/* ./data
    sudo chown -R $USER:$USER data
    ```

1. Adapt deposit-data.json to the following format:

    ```json
    [{},{},...]
    ```

1. Put keystores in the following format:

    * You need to escape all double quotes in the keystores so that curl accepts the data

    ```json
    {
      "keystores": [
        "<KEYSTORE_1>",
        "<KEYSTORE_2>"
      ],
      "passwords": [
        "PASSWORD_FOR_KEYSTORE_1",
        "PASSWORD_FOR_KEYSTORE_2"
      ]
    }
    ```

    * Furthermore put everything on one line

1. Add keystores to validator via keymanager api:

    ```bash
    # The bearer token is always the same for every kurtosis devnet
    curl -X POST "${VALIDATOR_NODE}/eth/v1/keystores" -H  "accept: application/json" -H  "Content-Type: application/json" -H "Authorization: Bearer 0x3ec0ad340bb9ca21e5593045b533d11d1b6784e03468af01db621db1804c2f0f" -d '<ABOVE_CREATED_JSON>'
    ```

1. Download [latest ethereal version](https://github.com/wealdtech/ethereal/releases) and send deposit-data to deposit contract:

    ```bash
    # --from and --privateKey reference kurtosis devnet prefunded accounts 
    ./ethereal beacon deposit --connection ${EXECUTION_NODE} --data=./output/deposit-data.json --address=0x4242424242424242424242424242424242424242 --from=0x8943545177806ED17B9F23F0a21ee5948eCaa776 --privatekey=bcdf20249abf0ed6d944c0288fad489e33f66b3960d9e6229c1cd214ed3bbe31 --allow-unknown-contract --wait
    ```

1. Check validator status:

    ```bash
    curl --location "${BEACON_NODE}/eth/v1/beacon/states/head/validators?id=<ONE_PUBKEY>"
    ```

    * You should see that validators are in pending state after one epoch
