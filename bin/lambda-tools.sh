#!/usr/bin/env bash

# A helper tool to assist us maintaining lambda functions
# Intention here is to keep this files and all its functions reusable for all Telemetry repositories

set -o errexit
set -o nounset

#####################################################################
## Beginning of the configurations ##################################

BASE_LOCATION="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_FULL_NAME=$(basename $BASE_LOCATION)
PROJECT_NAME=$(echo $PROJECT_FULL_NAME | sed 's/aws-lambda-//')

PATH_BUILD="${BASE_LOCATION}/build"
PATH_CF_TEMPLATE="${PATH_BUILD}/${PROJECT_NAME}-cf-template.yaml"
PATH_SAM_RESOURCES="${BASE_LOCATION}/resources/aws-sam-cli/"

S3_TELEMETRY_LAMBDA_ROOT="telemetry-internal-base-lambda-artifacts"
S3_LAMBDA_SUB_FOLDER="build-${PROJECT_FULL_NAME}"
S3_ADDRESS="s3://${S3_TELEMETRY_LAMBDA_ROOT}/${S3_LAMBDA_SUB_FOLDER}"

## End of the configurations ########################################
#####################################################################

# Prepare dependencies and build the Lambda function code using SAM
assemble() {
  print_begins

  mkdir -p ${PATH_BUILD}
  poetry export --without-hashes --format requirements.txt --output ${PATH_BUILD}/requirements.txt
  SAM_CLI_TELEMETRY=0 poetry run sam build ${SAM_USE_CONTAINER:=""} --template-file ${PATH_SAM_RESOURCES}/template.yaml --manifest ${PATH_BUILD}/requirements.txt --region eu-west-2

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
  rename_artifacts_in_s3
  publish_checksum_file

  print_completed
}

# Package and upload artifacts to S3 using poetry installed SAM
publish_artifacts_to_s3() {
  print_begins

  export_version

  # Unfortunately Poetry won't allow
  # us to add awscli to the --dev dependencies due to transitive
  # dependency conflicts with aws-sam-cli. Until the conflicts are
  # resolved we have to use pip to install awscli.

  # Commenting this as I dont see why it is needed here also I expect awscli be installed in the codebuild instance
  # pip install awscli

  SAM_CLI_TELEMETRY=0 poetry run sam package --region eu-west-2 \
    --s3-bucket ${S3_TELEMETRY_LAMBDA_ROOT} \
    --s3-prefix ${S3_LAMBDA_SUB_FOLDER} \
    --output-template-file=${PATH_CF_TEMPLATE}

  print_completed
}

# Download the artifacts zip file and generate its checksum file to be stored alongside it
publish_checksum_file() {
  print_begins

  export_version
  export FILE_NAME="aws-lambda-${PROJECT_NAME}.${VERSION}.zip"
  export HASH_FILE_NAME="${FILE_NAME}.base64sha256.txt"
  aws s3 cp ${S3_ADDRESS}/${FILE_NAME} ${PATH_BUILD}/${FILE_NAME}
  echo -n "${PATH_BUILD}/${FILE_NAME}" | openssl dgst -binary -sha1 | openssl base64 >${PATH_BUILD}/${HASH_FILE_NAME}
  aws s3 cp ${PATH_BUILD}/${HASH_FILE_NAME} ${S3_ADDRESS}/${HASH_FILE_NAME} \
    --content-type text/plain --acl=bucket-owner-full-control

  print_completed
}

# Rename SAM generated package to the expected format by terraform,
#   to be picked up during provisioning of the AWS "Lambda function" resource
rename_artifacts_in_s3() {
  print_begins

  export_version
  export S3_KEY_FILENAME=$(grep S3Key ${PATH_CF_TEMPLATE} | cut -d : -f 2 | cut -d / -f 2 | sed 's/\s*//g')

  # Using mv instead of cp will require updating the codebuild's service-role to grant DeleteObject permission
  aws s3 mv ${S3_ADDRESS}/${S3_KEY_FILENAME} ${S3_ADDRESS}/aws-lambda-${PROJECT_NAME}.${VERSION}.zip \
    --acl=bucket-owner-full-control

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
  echo -e " - assemble\t\t\t Prepare dependencies and build the Lambda function code using SAM"
  echo -e " - prepare_release\t\t Bump the function's version when appropriate"
  echo -e " - publish\t\t\t Package and share artifacts by running assemble, publish_artifacts_to_s3, rename_artifacts_in_s3 and publish_checksum_file commands"
  echo -e " - publish_artifacts_to_s3\t Uses SAM to Package and upload artifacts to ${S3_ADDRESS}"
  echo -e " - publish_checksum_file\t Generate a checksum for the artifacts zip file and store in the same S3 location (${S3_LAMBDA_SUB_FOLDER})"
  echo -e " - rename_artifacts_in_s3\t Rename the artifact published by SAM to ${S3_ADDRESS} to expected, versioned file name"
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
  echo -e "PROJECT_FULL_NAME:\t\t${PROJECT_FULL_NAME}"
  echo -e "PROJECT_NAME:\t\t\t${PROJECT_NAME}"
  echo
  echo -e "PATH_BUILD:\t\t\t${PATH_BUILD}"
  echo -e "PATH_CF_TEMPLATE:\t\t${PATH_CF_TEMPLATE}"
  echo -e "PATH_SAM_RESOURCES:\t\t${PATH_SAM_RESOURCES}"
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
  functions="help assemble publish_s3 rename_s3_file publish publish_checksum_file prepare_release print_configs cut_release"
  [[ $functions =~ (^|[[:space:]])"$function"($|[[:space:]]) ]] || (echo -e "\n\"$function\" is not a valid command. Try \"$0 help\" for more details" && exit 2)

  $function
}

main "$@"
## End of the Entry point ###########################################
#####################################################################
