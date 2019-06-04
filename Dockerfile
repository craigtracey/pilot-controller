FROM python:2-alpine3.8

RUN apk update && apk add build-base git libffi-dev openssl-dev

WORKDIR /tmp/
COPY pilot /tmp/pilot/
COPY .git /tmp/.git/
COPY setup.py /tmp/setup.py
COPY setup.cfg /tmp/setup.cfg
COPY requirements.txt /tmp/requirements.txt

RUN pip install -r requirements.txt
RUN python setup.py install
