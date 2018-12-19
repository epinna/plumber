FROM debian:buster

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
  apt-get -y install python3-pip && \
  pip3 install motor aiohttp

RUN mkdir -p /plumber/

COPY api /plumber/api

CMD /plumber/api/app.py
