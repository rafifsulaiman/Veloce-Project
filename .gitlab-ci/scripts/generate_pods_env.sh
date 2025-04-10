#!/bin/sh

echo "Generating env.yaml..."

# Init pods env
env | grep -E '^(PODS_|DB_)' | sed '1s/^/name=value\n/' | yq -p csv --csv-separator '=' ".[].value |= to_string" > env.yaml

echo "env.yaml generated"
