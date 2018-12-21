alexa-subdomains-webservers
===========================

This pipeline daily gets the updated Alexa 1K top websites lists, enumerates their subdomains using [crt.sh](https://crt.sh) service, and finally collect the screenshots of the HTTPS websites in a folder.

This is an example on how to consume the Plumber API using shell scripts. It is deliberately simple and not optimized and does not manage errors and other corner cases.

Stage 1
-------

The first stage has a single container that collects the Alexa top 1K every day.

### /stage-1/scripts/01-get-alexa-top-1K.sh

```
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
```

### docker-compose.yml

```
services:
  stage-1:
    deploy:
      replicas: 1 # Single container
    environment:
      IDLE: 43200 # Run scripts every 12H
```

Stage 2
-------

The second stage enumerates the subdomains.

### /stage-2/scripts/01-enumerate-subdomains.sh

```
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
```

### docker-compose.yml

```
services:
  stage-2:
    deploy:
      replicas: 3 # Set of 3 containers
    environment:
      IDLE: 0 # No delay between runs
```

Stage 3
-------

The third stage gets a screenshot of every HTTPS website in the subdomains and save it in a folder on the host.

### /stage-3/scripts/01-get-screenshot.sh

```
#!/bin/bash

# Pop subdomain from pipeline
SUBDOMAIN=$(curl -s "http://plumber/$STAGE/pop?format=plain") || { exit; } 

# Wait if pipe is empty
test -z "$SUBDOMAIN" && { sleep 10; exit; }

# Check if site responds, and get a screenshot
curl --max-time 20 -s "https://$SUBDOMAIN" -o /dev/null && \
  xvfb-run --server-args="-screen 0, 1024x768x24" cutycapt "--url=https://$SUBDOMAIN" "--out=/tmp/captures/$SUBDOMAIN.jpg" 2>/dev/null
```

### docker-compose.yml

```
  stage-3:
    deploy:
      replicas: 10 # Set of 10 containers
    environment:
      STAGE: 3
    volumes:
      - /tmp/captures/:/tmp/captures/
```

Usage
=====

Use `docker-compose` to manage the pipeline.

```
docker-compose up -d                                    # Start the pipeline
docker-compose logs -f stage-1 stage-2 stage-3 plumber  # Print the logs of stages and API
docker-compose down                                     # Shut down the pipeline
```
