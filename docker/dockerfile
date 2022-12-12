FROM python:3.10-alpine3.15

RUN python3 -m pip install \
  colorama==0.4.6 \
  dataclass_wizard==0.22.0 \
  pyyaml==6.0 \
  requests==2.28.1

RUN adduser -D app
USER app

WORKDIR /home/app

COPY config ./config
COPY duties ./duties

ENTRYPOINT [ "python", "duties/duties.py" ]
