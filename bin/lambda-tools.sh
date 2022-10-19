#!/usr/bin/env bash

# A helper tool to assist us maintaining lambda functions
# Intention here is to keep this files and all its functions reusable for all Telemetry repositories

set -o errexit
set -o nounset

#####################################################################
## Beginning of the configurations ##################################

BASE_LOCATION="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LAMBDA_ZIP_NAME="lambda.zip"
PATH_BUILD="${BASE_LOCATION}/build"
PROJECT_FULL_NAME="aws-lambda-ec2-launch-checks"

S3_TELEMETRY_LAMBDA_ROOT="telemetry-internal-base-lambda-artifacts"
S3_LAMBDA_SUB_FOLDER="build-${PROJECT_FULL_NAME}"
S3_ADDRESS="s3://${S3_TELEMETRY_LAMBDA_ROOT}/${S3_LAMBDA_SUB_FOLDER}"

## End of the configurations ########################################
#####################################################################

debug_env(){
  echo BASE_LOCATION="${BASE_LOCATION}"
  echo PROJECT_FULL_NAME=${PROJECT_FULL_NAME}
  echo PATH_BUILD="${PATH_BUILD}"
  echo S3_TELEMETRY_LAMBDA_ROOT="${S3_TELEMETRY_LAMBDA_ROOT}"
  echo S3_ADDRESS="${S3_ADDRESS}"
}

open_shell() {
    print_begins

    poetry export --without-hashes --format requirements.txt --with dev --output "requirements-tests.txt"
    docker run -it \
               --rm \
               --volume "${BASE_LOCATION}":/data \
               --workdir /data \
               --env REQUIREMENTS_FILE="requirements-tests.txt" \
               --env VENV_NAME="venv" \
               python:$(cat "${BASE_LOCATION}/.python-version")-slim-buster /data/bin/entrypoint.sh /bin/bash

    print_completed
}

# Prepare dependencies and run unit tests in a Docker environment
unittest() {
  print_begins

  poetry export --without-hashes --format requirements.txt --with dev --output "requirements-tests.txt"
  docker run --rm \
             --tty \
             --volume "${BASE_LOCATION}":/data \
             --workdir /data \
             --env REQUIREMENTS_FILE="requirements-tests.txt" \
             --env VENV_NAME="venv" \
             python:$(cat "${BASE_LOCATION}/.python-version")-slim-buster /data/bin/entrypoint.sh /data/bin/run-tests.sh

  print_completed
}

# Prepare dependencies and build the Lambda function code using SAM
assemble() {
  print_begins

  poetry export --without-hashes --format requirements.txt --output "requirements.txt"
  docker run --rm \
             --tty \
             --volume "${BASE_LOCATION}":/data \
             --workdir /data \
             --env LAMBDA_ZIP_NAME=${LAMBDA_ZIP_NAME} \
             --env REQUIREMENTS_FILE="requirements.txt" \
             --env VENV_NAME="venv_assemble" \
             python:$(cat "${BASE_LOCATION}/.python-version")-slim-buster /data/bin/entrypoint.sh /data/bin/assemble-lambda.sh

  print_completed
}

# Creates a release tag in the repository
cut_release() {
  print_begins

  poetry run cut-release

  print_completed
}

# Bump the function's version when appropriate
prepare_release() {
  print_begins

  poetry run prepare-release
  export_version

  print_completed
}

# Take all the necessary steps to build and publish both lambda function's zip and checksum files
publish() {
  print_begins

  assemble
  publish_artifacts_to_s3
  publish_checksum_file

  print_completed
}

# Package and upload artifacts to S3 using poetry installed SAM
publish_artifacts_to_s3() {
  print_begins

  export_version

  aws s3 cp "${PATH_BUILD}/${LAMBDA_ZIP_NAME}" "${S3_ADDRESS}/${PROJECT_FULL_NAME}.${VERSION}.zip" \
      --acl=bucket-owner-full-control

  print_completed
}

# Download the artifacts zip file and generate its checksum file to be stored alongside it
publish_checksum_file() {
  print_begins

  export_version
  export FILE_NAME="${PROJECT_FULL_NAME}.${VERSION}.zip"
  export HASH_FILE_NAME="${FILE_NAME}.base64sha256"
  aws s3 cp "${S3_ADDRESS}/${FILE_NAME}" "${PATH_BUILD}/${FILE_NAME}"
  openssl dgst -sha256 -binary "${PATH_BUILD}/${FILE_NAME}" | openssl enc -base64 >"${PATH_BUILD}/${HASH_FILE_NAME}"
  aws s3 cp "${PATH_BUILD}/${HASH_FILE_NAME}" "${S3_ADDRESS}/${HASH_FILE_NAME}" \
    --content-type text/plain --acl=bucket-owner-full-control

  print_completed
}

#####################################################################
## Beginning of the helper methods ##################################

export_version() {

  if [ ! -f ".version" ]; then
    echo ".version file not found! Have you run prepare_release command?"
    exit 1
  fi

  export VERSION=$(cat .version)

}

help() {
  echo "$0 Provides set of commands to assist you with day-to-day tasks when working in this project"
  echo
  echo "Available commands:"
  echo -e " - assemble\t\t\t Prepare dependencies and build the Lambda function code using Docker"
  echo -e " - prepare_release\t\t Bump the function's version when appropriate"
  echo -e " - publish\t\t\t Package and share artifacts by running assemble, publish_artifacts_to_s3 and publish_checksum_file commands"
  echo -e " - publish_artifacts_to_s3\t Uses SAM to Package and upload artifacts to ${S3_ADDRESS}"
  echo -e " - publish_checksum_file\t Generate a checksum for the artifacts zip file and store in the same S3 location (${S3_LAMBDA_SUB_FOLDER})"
  echo -e " - cut_release\t\t Creates a release tag in the repository"
  echo
}

print_begins() {
  echo -e "\n-------------------------------------------------"
  echo -e ">>> ${FUNCNAME[1]} Begins\n"
}

print_completed() {
  echo -e "\n### ${FUNCNAME[1]} Completed!"
  echo -e "-------------------------------------------------"
}

print_configs() {
  echo -e "BASE_LOCATION:\t\t\t${BASE_LOCATION}"
  echo -e "PATH_BUILD:\t\t\t${PATH_BUILD}"
  echo -e "PROJECT_FULL_NAME:\t\t${PROJECT_FULL_NAME}"
  echo
  echo -e "S3_TELEMETRY_LAMBDA_ROOT:\t${S3_TELEMETRY_LAMBDA_ROOT}"
  echo -e "S3_LAMBDA_SUB_FOLDER:\t\t${S3_LAMBDA_SUB_FOLDER}"
  echo -e "S3_ADDRESS:\t\t\t${S3_ADDRESS}"
}

## End of the helper methods ########################################
#####################################################################

#####################################################################
## Beginning of the Entry point #####################################
main() {
  # Validate command arguments
  [ "$#" -ne 1 ] && help && exit 1
  function="$1"
  functions="help debug_env open_shell unittest assemble publish_s3 rename_s3_file publish publish_checksum_file prepare_release print_configs cut_release"
  [[ $functions =~ (^|[[:space:]])"$function"($|[[:space:]]) ]] || (echo -e "\n\"$function\" is not a valid command. Try \"$0 help\" for more details" && exit 2)

  # Ensure build folder is available
  mkdir -p "${PATH_BUILD}"

  $function
}

main "$@"
## End of the Entry point ###########################################
#####################################################################
