#!/bin/bash

# Pop subdomain from pipeline
SUBDOMAIN=$(curl -s "http://plumber/$STAGE/pop?format=plain") || { exit; } 

# Wait if pipe is empty
test -z "$SUBDOMAIN" && { sleep 10; exit; }

# Check if site responds, and get a screenshot
curl --max-time 20 -s "https://$SUBDOMAIN" -o /dev/null && \
  xvfb-run --server-args="-screen 0, 1024x768x24" cutycapt "--url=https://$SUBDOMAIN" "--out=/tmp/captures/$SUBDOMAIN.jpg" 2>/dev/null
