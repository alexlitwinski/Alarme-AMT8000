#!/usr/bin/with-contenv bashio
# ==============================================================================
# AMT-8000 Alarm Manager - Startup Script
# ==============================================================================

bashio::log.info "Starting AMT-8000 Alarm Manager..."

# Read configuration from options
export AMT_HOST="$(bashio::config 'host')"
export AMT_PORT="$(bashio::config 'port')"
export AMT_PASSWORD="$(bashio::config 'password')"
export AMT_UPDATE_INTERVAL="$(bashio::config 'update_interval')"
export INGRESS_PATH="$(bashio::addon.ingress_entry)"

bashio::log.info "Connecting to AMT-8000 at ${AMT_HOST}:${AMT_PORT}"
bashio::log.info "Update interval: ${AMT_UPDATE_INTERVAL}s"
bashio::log.info "Ingress path: ${INGRESS_PATH}"

# Start Flask server
cd /app
exec python3 server.py
