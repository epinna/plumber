#!/bin/bash

TOP_DOMAINS_QTY=1000

  # Download and unzip the Alexa top million websites
rm -f top-1m.csv.zip top-1m.csv 2>/dev/null
curl -sS http://s3.amazonaws.com/alexa-static/top-1m.csv.zip -o top-1m.csv.zip
unzip -qq top-1m.csv.zip

# Push the top domains to the next queue
head -n $TOP_DOMAINS_QTY top-1m.csv | \
  cut -d, -f2 | \
  curl -s "http://plumber/$NEXT_STAGE/push?format=plain&push_if_new=true" --data-binary @- -o /dev/null
