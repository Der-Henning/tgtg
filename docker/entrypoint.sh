#!/bin/sh
set -e

echo "Updating UID and GID to ${UID}:${GID}"
usermod -u ${UID} tgtg && groupmod -g ${GID} tgtg
chown -R ${UID}:${GID} /tokens /logs

echo "Starting tgtg"
exec runuser -u tgtg -- "$@"
