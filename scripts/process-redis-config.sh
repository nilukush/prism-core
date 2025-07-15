#!/bin/bash

# Process Redis configuration template with environment variables

set -euo pipefail

# Source environment file if provided
if [ -f "${1:-}" ]; then
    source "$1"
fi

# Set defaults if not provided
REDIS_PASSWORD=${REDIS_PASSWORD:-redis_password}
REDIS_MAX_MEMORY=${REDIS_MAX_MEMORY:-512mb}
REDIS_EVICTION_POLICY=${REDIS_EVICTION_POLICY:-allkeys-lru}
REDIS_LOG_LEVEL=${REDIS_LOG_LEVEL:-notice}
REDIS_SLOWLOG_TIME=${REDIS_SLOWLOG_TIME:-10000}
REDIS_SLOWLOG_MAX_LEN=${REDIS_SLOWLOG_MAX_LEN:-128}
REDIS_MAX_CLIENTS=${REDIS_MAX_CLIENTS:-10000}

# Process template
envsubst < redis.conf.template > redis.conf

echo "Redis configuration processed successfully"