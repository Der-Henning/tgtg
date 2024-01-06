#!/bin/sh
set -e

echo "Updating UID and GID to ${UID}:${GID}"
usermod -u ${UID} tgtg && groupmod -g ${GID} tgtg
chown -R ${UID}:${GID} ${TGTG_TOKEN_PATH} ${LOGS_PATH}

exec runuser -u tgtg -- "$@"
