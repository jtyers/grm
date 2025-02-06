#!/bin/sh

set -eu
dn=$(dirname "$0")

export PIPENV_PIPFILE="$dn/Pipfile"
export PYTHONPATH=$dn/src

if [ ${DEBUG:-0} -eq 1 ]; then
    pipenv run \
      pudb \
      -m grm._internal.main \
      "$@"
else
    pipenv run \
      grm \
      "$@"
fi
