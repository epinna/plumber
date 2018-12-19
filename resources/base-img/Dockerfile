FROM debian:buster

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
  apt-get -y install curl python3-pip parallel jq && \
  pip3 install pymongo requests

RUN mkdir -p /plumber/scripts/

COPY libs /plumber/libs
COPY run-scripts.sh /plumber/run-scripts.sh

WORKDIR /tmp/

ENV PYTHONPATH "/plumber/libs/python/"
