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
        PIPELINE_NAME=$2
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
    echo "ERROR Pipeline folder is missing"
    print_help
    exit 1
  }

  PIPELINE_FOLDER=${POSITIONAL[0]}

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

  $0 [options] <pipeline folder> [# of stages]

Options:

  -f, --force         Backup the existing folder and re-init the pipeline
  -n, --name          Specify project name (default: pipeline folder name) 
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
function check_pipeline_folder() {

  test -z "$PIPELINE_NAME" && PIPELINE_NAME="$(basename $PIPELINE_FOLDER)"

  printf "[+] $PIPELINE_NAME folder pipeline $PIPELINE_FOLDER.. "
    
  # Check pipeline folder presence
  if [[ -d "${PIPELINE_FOLDER}" ]]; then

    # Exit if already there
    test "${FORCE}" != "YES" && {
      echo -e "ERROR\n    Folder exists, run with '-f' to backup and recreate new structure" 
      exit 1
    }

    # Backup if forcing overwrite
    BACKUP_FOLDER="$(mktemp -d)"
    mv "${PIPELINE_FOLDER}" "${BACKUP_FOLDER}" || {
     echo -e "ERROR\n    Error doing a backup of ${PIPELINE_FOLDER}" 
     exit 1
    }

    # Create pipeline folder
    mkdir -p $PIPELINE_FOLDER || {
      echo -e "ERROR\n    Error creating ${PIPELINE_FOLDER}" 
      exit 1
    }

    echo -e "OK\n    Existing folder has been backup as ${BACKUP_FOLDER}"

  else

    # Create pipeline folder
    mkdir -p $PIPELINE_FOLDER || {
      echo -e "ERROR\n    Error creating ${PIPELINE_FOLDER}" 
      exit 1
    }

    echo "OK"
  fi

}

function add_pipeline_compose() {

  printf "[+] $PIPELINE_NAME pipeline compose file.. "

  PIPELINE_COMPOSEFILE="$PIPELINE_FOLDER/docker-compose.override.yml"
  envsubst < resources/pipeline/docker-compose.override.yml > "${PIPELINE_COMPOSEFILE}" || {
   echo -e "ERROR\n    Error creating ${PIPELINE_COMPOSEFILE}" 
   exit 1
  }
  echo "OK"
}

function copy_stage_data() {

  printf "[+] $STAGE_NAME stage data.. "

  cp -r resources/pipeline/data "${STAGE_FOLDER}" || {
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

  envsubst < resources/pipeline/docker-compose.yml >> $STAGE_COMPOSEFILE || {
   echo -e "ERROR\n    Error creating ${STAGE_COMPOSEFILE}" 
   exit 1
  }


  echo "OK"

}

function start_stages_compose() {

  printf "[+] Init stages compose file.. "
  
  cp resources/pipeline/docker-compose.start.yml $STAGE_COMPOSEFILE || {
   echo -e "ERROR\n    Error creating ${STAGE_COMPOSEFILE}" 
   exit 1
  }

  echo "OK"

}

function build_workers_image() {

  printf "[+] Workers images.. "

  BUILDLOG="$(mktemp)"
  ( cd "${PIPELINE_FOLDER}" && docker-compose build ) &>$BUILDLOG || { 
    echo -e "ERROR\n    See $BUILDLOG for more info" 
    exit 1
  } 

  echo "OK"

}

parse_argument $@

build_base_image
build_api_image

test -z "$BUILD_ONLY" && { 

  check_pipeline_folder
  add_pipeline_compose

  STAGE_COMPOSEFILE="$PIPELINE_FOLDER/docker-compose.yml"

  start_stages_compose

  for ((STAGE_NUM=1;STAGE_NUM<=STAGES_QTY;STAGE_NUM++)); do

    STAGE_NAME="${PIPELINE_NAME}-stage-${STAGE_NUM}"
    STAGE_FOLDER="${PIPELINE_FOLDER}/stage-${STAGE_NUM}"
    STAGE_IMAGE="${STAGE_NAME}-img"

    copy_stage_data
    add_stage_compose

  done

}

build_workers_image
