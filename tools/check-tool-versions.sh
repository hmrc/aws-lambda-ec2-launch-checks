#!/usr/bin/env bash

### WARNING! This is a generated file and should ONLY be edited in https://github.com/hmrc/telemetry-lambda-resources

# Ensure .tool-versions (ASDF) and .<tool>-version (individual version managers) are referencing same version

# Variables
root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
asdf_version_file="$root_dir/.tool-versions"
declare -a tools=("poetry" "python" "terraform" "terragrunt")
all_synced=true

# Checks
for tool in "${tools[@]}"
do
  tool_version_file="$root_dir/.$tool-version"
  if [[ -f "${tool_version_file}" ]]; then
    if diff <(grep "$tool " "${asdf_version_file}" | awk '{print $2}') <(cat "${tool_version_file}") > /dev/null ; then
      echo "$tool version files are in sync"
    else
      echo -e "$tool version divergence detected!\t Cross-check $(basename "${asdf_version_file}") and $(basename "${tool_version_file}")"
      all_synced=false
    fi
  fi
done

# Verdict
if $all_synced; then
  exit 0
else
  exit 1
fi
