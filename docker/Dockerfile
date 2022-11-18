FROM python:3.10-alpine3.15

RUN python3 -m pip install \
  black==22.10.0 \
  colorama==0.4.6 \
  dataclass_wizard==0.22.0 \
  mypy==0.982 \
  pylint==2.15.3 \
  pyyaml==6.0 \
  requests==2.28.1 \
  rope==1.4.0 \
  types-pyyaml==6.0.12 \
  types-requests==2.28.11

RUN adduser -D app
USER app

WORKDIR /home/app

COPY config ./config
COPY duties ./duties

ENTRYPOINT [ "python", "duties/duties.py" ]
