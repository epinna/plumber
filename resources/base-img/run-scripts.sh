#!/bin/bash

export NEXT_STAGE=$((STAGE+1))

while :; do
    find /plumber/scripts/ \
    -maxdepth 1 \
    -type f \
    -executable | \
    sort -k 3 | \
    parallel -I{} --jobs ${CONCURRENT_SCRIPTS} \
      "echo [$(date '+%d-%m-%Y %H:%M:%S')] $(hostname) $(basename '{}'); exec '{}'"
    sleep ${IDLE}
done
