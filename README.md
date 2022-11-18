# eth-duties

CLI tool for printing upcoming validator duties to the console

## Run in Docker

build image

```bash
docker build -t tobiwo/eth-duties:latest -f docker/Dockerfile .
```

run container

```bash
docker run --rm --name eth-duties tobiwo/eth-duties:latest -v "123456, 456789" -b "http://locahost:5052"
```

run container on boot

```bash
docker run -d --restart always --name eth-duties tobiwo/eth-duties:latest -v "123456, 456789" -b "http://locahost:5052"
```

print logs

```bash
docker logs eth-duties --tail=20 -f
```
