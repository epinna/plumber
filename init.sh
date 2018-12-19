#!/bin/bash

set -a 

#Default container settings
IDLE=60               # Time between scripts execution
CONCURRENT_SCRIPTS=1  # Concurrency on scripts execution
REPLICAS=1            # Instances in a stage

BASE_IMAGE=plumber-base-img
API_IMAGE=plumber-api-img

function parse_argument() {

  # Argument parsing
  POSITIONAL=()
  while [[ $# -gt 0 ]]; do
  key="$1"

    case $key in
        -f|--force)
        FORCE=YES
        shift 
        ;;
        --no-cache)
        NO_CACHE=" --no-cache "
        shift 
        ;;
        --build-only)
        BUILD_ONLY=YES
        shift 
        ;;
        -n|--name)
        CLUSTER_NAME=$2
        shift 
        shift 
        ;;
        *) 
        POSITIONAL+=("$1") 
        shift
        ;;
    esac

  done
  set -- "${POSITIONAL[@]}" # restore positional parameters

  test -z "${POSITIONAL[0]}" && {
    echo "ERROR Cluster folder is missing"
    print_help
    exit 1
  }

  CLUSTER_FOLDER=${POSITIONAL[0]}

  test $BUILD_ONLY && { return; }

  if ! [[ "${POSITIONAL[1]}" =~ ^[0-9]+$ ]] ; then
     echo "ERROR Stage number is missing or not a number" 
     print_help
     exit 1
  fi

  STAGES_QTY="${POSITIONAL[1]}"

}

function print_help() {
  cat << EOH

Usage:

  $0 [options] <cluster folder> [# of stages]

Options:

  -f, --force         Backup the existing folder and re-init the cluster
  -n, --name          Specify project name (default: cluster folder name) 
  --no-cache          Force rebuild of base image
  --build-only        Rebuild the base and the worker images only

EOH
}

function build_base_image() {

  printf "[+] Base image $BASE_IMAGE.. "

  BUILDLOG="$(mktemp)"
  docker build $NO_CACHE --tag $BASE_IMAGE resources/base-img/ &>$BUILDLOG || { 
    echo -e "ERROR\n    See $BUILDLOG for more info" 
    exit 1
  }

  echo "OK"

}

function build_api_image() {

  printf "[+] API image $API_IMAGE.. "

  BUILDLOG="$(mktemp)"
  docker build $NO_CACHE --tag $API_IMAGE resources/plumber-api/ &>$BUILDLOG || { 
    echo -e "ERROR\n    See $BUILDLOG for more info" 
    exit 1
  }

  echo "OK"

}
function check_cluster_folder() {

  test -z "$CLUSTER_NAME" && CLUSTER_NAME="$(basename $CLUSTER_FOLDER)"

  printf "[+] $CLUSTER_NAME folder cluster $CLUSTER_FOLDER.. "
    
  # Check cluster folder presence
  if [[ -d "${CLUSTER_FOLDER}" ]]; then

    # Exit if already there
    test "${FORCE}" != "YES" && {
      echo -e "ERROR\n    Folder exists, run with '-f' to backup and recreate new structure" 
      exit 1
    }

    # Backup if forcing overwrite
    BACKUP_FOLDER="$(mktemp -d)"
    mv "${CLUSTER_FOLDER}" "${BACKUP_FOLDER}" || {
     echo -e "ERROR\n    Error doing a backup of ${CLUSTER_FOLDER}" 
     exit 1
    }

    # Create cluster folder
    mkdir -p $CLUSTER_FOLDER || {
      echo -e "ERROR\n    Error creating ${CLUSTER_FOLDER}" 
      exit 1
    }

    echo -e "OK\n    Existing folder has been backup as ${BACKUP_FOLDER}"

  else

    # Create cluster folder
    mkdir -p $CLUSTER_FOLDER || {
      echo -e "ERROR\n    Error creating ${CLUSTER_FOLDER}" 
      exit 1
    }

    echo "OK"
  fi

}

function add_cluster_compose() {

  printf "[+] $CLUSTER_NAME cluster compose file.. "

  CLUSTER_COMPOSEFILE="$CLUSTER_FOLDER/docker-compose.override.yml"
  envsubst < resources/cluster/docker-compose.override.yml > "${CLUSTER_COMPOSEFILE}" || {
   echo -e "ERROR\n    Error creating ${CLUSTER_COMPOSEFILE}" 
   exit 1
  }
  echo "OK"
}

function copy_stage_data() {

  printf "[+] $STAGE_NAME stage data.. "

  cp -r resources/cluster/data "${STAGE_FOLDER}" || {
   echo -e "ERROR\n    Error copying data to ${STAGE_FOLDER}" 
   exit 1
  }

  mkdir -p "${STAGE_FOLDER}/scripts" || {
   echo -e "ERROR\n    Error creating scripts folder in ${STAGE_FOLDER}" 
   exit 1
  }

  echo "OK"
}

function add_stage_compose() {

  printf "[+] Add $STAGE_NAME compose file.. "

  envsubst < resources/cluster/docker-compose.yml >> $STAGE_COMPOSEFILE || {
   echo -e "ERROR\n    Error creating ${STAGE_COMPOSEFILE}" 
   exit 1
  }


  echo "OK"

}

function start_stages_compose() {

  printf "[+] Init stages compose file.. "
  
  cp resources/cluster/docker-compose.start.yml $STAGE_COMPOSEFILE || {
   echo -e "ERROR\n    Error creating ${STAGE_COMPOSEFILE}" 
   exit 1
  }

  echo "OK"

}

function build_workers_image() {

  printf "[+] Workers images.. "

  BUILDLOG="$(mktemp)"
  ( cd "${CLUSTER_FOLDER}" && docker-compose build ) &>$BUILDLOG || { 
    echo -e "ERROR\n    See $BUILDLOG for more info" 
    exit 1
  } 

  echo "OK"

}

parse_argument $@

build_base_image
build_api_image

test -z "$BUILD_ONLY" && { 

  check_cluster_folder
  add_cluster_compose

  STAGE_COMPOSEFILE="$CLUSTER_FOLDER/docker-compose.yml"

  start_stages_compose

  for ((STAGE_NUM=1;STAGE_NUM<=STAGES_QTY;STAGE_NUM++)); do

    STAGE_NAME="${CLUSTER_NAME}-stage-${STAGE_NUM}"
    STAGE_FOLDER="${CLUSTER_FOLDER}/stage-${STAGE_NUM}"
    STAGE_IMAGE="${STAGE_NAME}-img"

    copy_stage_data
    add_stage_compose

  done

}

build_workers_image
