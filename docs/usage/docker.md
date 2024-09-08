# Docker

The docker image repository can be found [here](https://hub.docker.com/r/tobiwo/eth-duties).

## Build image

If you want to build on your own:

```bash
docker buildx build -t tobiwo/eth-duties:latest -f docker/dockerfile .
```

## Run in Docker

1. Run container using space separation for --validators

    ```bash
    docker run \
    --rm \
    --name eth-duties \
    tobiwo/eth-duties:latest \
    --validators 123456 456789 \
    --validators 0x98... \
    --validators "111;My_Validator" "222;Validator2" \
    --beacon-node http://localhost:5052
    ```

1. Run container on boot using comma separation for --validators

    ```bash
    docker run \
    -d \
    --restart always \
    --name eth-duties \
    tobiwo/eth-duties:latest \
    --validators 123456,456789 \
    --validators "111;My_Validator","222;Validator2" \
    --beacon-node http://localhost:5052
    ```

1. Print logs

    ```bash
    docker logs eth-duties --tail=20 -f
    ```

### Docker compose

You can find multiple `docker-compose` examples/templates in the `docker` folder of this repository. Please see the example description in the header of the respective file. You need to replace all placeholders with actual values before using it. If you do not copy the compose to your own setup the commands for starting the container would be (from the root of this repo):

```bash
# Using compose plugin for docker
docker compose -f docker/compose.yaml up -d

# Using docker-compose binary
docker-compose -f docker/compose.yaml up -d
```
