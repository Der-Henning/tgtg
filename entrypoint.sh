#!/bin/bash
set -e

usermod -u ${UID} tgtg && groupmod -g ${GUID} tgtg

chown -R tgtg:tgtg /app /tokens

su - tgtg

exec "$@"
