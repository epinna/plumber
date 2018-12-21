#!/bin/bash 

# Pop domain from pipeline
DOMAIN=$(curl -s "http://plumber/$STAGE/pop?format=plain") || { exit; }

# Wait if pipe is empty
test -z "$DOMAIN" && { sleep 10; exit; }

# Query crt.sh
CERT_DATA=$(curl --max-time 20 -s "https://crt.sh?q=%.$DOMAIN&output=json") || { exit; }

# Parse list of subdomains
SUBDOMAINS_LIST=$(jq --raw-output 'select(.name_value|startswith("*.")|not)|.name_value' <<< "$CERT_DATA") || { exit; }

# Push to the next stage
echo "$SUBDOMAINS_LIST" | curl -s "http://plumber/$NEXT_STAGE/push?format=plain&push_if_new=true" --data-binary @- -o /dev/null
