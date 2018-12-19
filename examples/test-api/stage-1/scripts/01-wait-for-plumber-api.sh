#!/bin/bash

# Wait until the http server is serving
until $(curl --output /dev/null --silent http://plumber/_healthcheck); do
    sleep 1
done
