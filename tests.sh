#!/bin/bash

set -eu

function help()
{
    echo ""
    echo "fix-lint       Fix linting problems"
    echo "lint           Run the code linters"
    echo "mypy           Type check the code"
    echo ""
    exit 1
}

function fix_lint()
{
    echo "Formatting with black..."
    black --skip-string-normalization -l 79 ./
    echo "Formatting with isort..."
    isort --profile black --force-grid-wrap 6 ./
}

function lint()
{
    echo "Checking with black..."
    black --check --diff --skip-string-normalization -l 79 ./
    echo "Checking with isort..."
    isort --check-only --df --profile black --force-grid-wrap 6 ./
}

function mypy()
{
    command mypy ./
}

if [ $# -eq 0 ] || [ "$1" == "-h" ] || [ "$1" == "--help" ] || [ "$1" == "help" ]  ; then
  help
fi

command=${1//-/_}
$command "${@:2}"
