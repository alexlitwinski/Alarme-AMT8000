"""
AMT-8000 Alarm Manager - Flask Web Server
Provides REST API and serves the web dashboard via Home Assistant Ingress.
"""

import os
import json
import time
import logging
import threading
from flask import Flask, render_template, jsonify, request

from amt8000_client import AMT8000Client, CommunicationError, AuthError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("amt8000-server")

# Configuration from environment variables (set by run.sh via bashio)
# Try loading from options.json (HA Add-on path)
OPTIONS_PATH = "/data/options.json"
options = {}
if os.path.exists(OPTIONS_PATH):
    try:
        with open(OPTIONS_PATH, "r") as f:
            options = json.load(f)
        logger.info("Successfully loaded configuration options from Home Assistant")
    except Exception as e:
        logger.error(f"Error loading options.json: {e}")

AMT_HOST = options.get("host") or os.environ.get("AMT_HOST", "192.168.1.100")
AMT_PORT = int(options.get("port") or os.environ.get("AMT_PORT", "9009"))
AMT_PASSWORD = options.get("password") or os.environ.get("AMT_PASSWORD", "123456")
UPDATE_INTERVAL = int(options.get("update_interval") or os.environ.get("AMT_UPDATE_INTERVAL", "4"))
INGRESS_PATH = os.environ.get("INGRESS_PATH", "")

# Custom names maps (allow flexible custom naming for zones and partitions)
CUSTOM_ZONES = {int(z["number"]): z["name"] for z in options.get("zones", []) if "number" in z and "name" in z}
CUSTOM_PARTITIONS = {int(p["number"]): p["name"] for p in options.get("partitions", []) if "number" in p and "name" in p}

logger.info(f"Custom Zone Names Configured: {len(CUSTOM_ZONES)}")
logger.info(f"Custom Partition Names Configured: {len(CUSTOM_PARTITIONS)}")

# Create Flask app
app = Flask(__name__, static_folder="static", template_folder="templates")

VERSION = "1.3.0"

# Create AMT-8000 client
client = AMT8000Client(AMT_HOST, AMT_PORT, AMT_PASSWORD)

# Status cache
status_cache = {
    "data": None,
    "timestamp": 0,
    "error": None,
    "connected": False,
}
cache_lock = threading.Lock()


def update_status_cache():
    """Background thread to periodically update the status cache."""
    global status_cache
    consecutive_errors = 0
    max_backoff = 60

    while True:
        try:
            data = client.get_status()
            with cache_lock:
                status_cache = {
                    "data": data,
                    "timestamp": time.time(),
                    "error": None,
                    "connected": True,
                }
            consecutive_errors = 0
            logger.debug("Status updated successfully")
        except AuthError as e:
            with cache_lock:
                status_cache["error"] = f"Autenticação falhou: {e.message}"
                status_cache["connected"] = False
            logger.error(f"Auth error: {e.message}")
            consecutive_errors += 1
        except CommunicationError as e:
            with cache_lock:
                status_cache["error"] = f"Erro de conexão: {e.message}"
                status_cache["connected"] = False
            logger.error(f"Communication error: {e.message}")
            consecutive_errors += 1
        except Exception as e:
            with cache_lock:
                status_cache["error"] = f"Erro: {str(e)}"
                status_cache["connected"] = False
            logger.error(f"Unexpected error: {str(e)}")
            consecutive_errors += 1

        # Exponential backoff on errors
        if consecutive_errors > 0:
            wait = min(UPDATE_INTERVAL * (2 ** min(consecutive_errors, 5)), max_backoff)
        else:
            wait = UPDATE_INTERVAL

        time.sleep(wait)


# ============================================================================
# Web Routes
# ============================================================================

@app.route("/")
def index():
    """Serve the main dashboard page."""
    return render_template("index.html", ingress_path=INGRESS_PATH, version=VERSION)


# ============================================================================
# API Routes
# ============================================================================

@app.route("/api/status")
def api_status():
    """Return the current alarm panel status."""
    with cache_lock:
        if status_cache["data"] is None and status_cache["error"]:
            return jsonify({
                "success": False,
                "error": status_cache["error"],
                "connected": False,
            }), 503

        # Convert zone/partition keys to strings for JSON and apply custom names
        data = status_cache["data"]
        if data:
            response_data = dict(data)
            
            response_data["zones"] = {}
            for k, v in data.get("zones", {}).items():
                zone_dict = dict(v)
                zone_dict["name"] = CUSTOM_ZONES.get(int(k), f"Zona {int(k):02d}")
                response_data["zones"][str(k)] = zone_dict
                
            response_data["partitions"] = {}
            for k, v in data.get("partitions", {}).items():
                part_dict = dict(v)
                part_dict["name"] = CUSTOM_PARTITIONS.get(int(k), f"Partição {int(k):02d}")
                response_data["partitions"][str(k)] = part_dict
        else:
            response_data = None

        return jsonify({
            "success": True,
            "data": response_data,
            "connected": status_cache["connected"],
            "lastUpdate": status_cache["timestamp"],
            "error": status_cache["error"],
        })


@app.route("/api/partition/<int:partition_id>/arm", methods=["POST"])
def api_arm_partition(partition_id):
    """Arm a specific partition."""
    try:
        result = client.arm_partition(partition_id)
        logger.info(f"Arm partition {partition_id}: {result}")
        if result.get("success"):
            with cache_lock:
                if status_cache["data"] and "partitions" in status_cache["data"]:
                    if partition_id in status_cache["data"]["partitions"]:
                        status_cache["data"]["partitions"][partition_id]["armed"] = True
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error arming partition {partition_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/partition/<int:partition_id>/disarm", methods=["POST"])
def api_disarm_partition(partition_id):
    """Disarm a specific partition."""
    try:
        result = client.disarm_partition(partition_id)
        logger.info(f"Disarm partition {partition_id}: {result}")
        if result.get("success"):
            with cache_lock:
                if status_cache["data"] and "partitions" in status_cache["data"]:
                    if partition_id in status_cache["data"]["partitions"]:
                        status_cache["data"]["partitions"][partition_id]["armed"] = False
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error disarming partition {partition_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/partition/all/arm", methods=["POST"])
def api_arm_all():
    """Arm all partitions."""
    try:
        result = client.arm_partition(0)
        logger.info(f"Arm all partitions: {result}")
        if result.get("success"):
            with cache_lock:
                if status_cache["data"] and "partitions" in status_cache["data"]:
                    for pid in status_cache["data"]["partitions"]:
                        status_cache["data"]["partitions"][pid]["armed"] = True
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error arming all partitions: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/partition/all/disarm", methods=["POST"])
def api_disarm_all():
    """Disarm all partitions."""
    try:
        result = client.disarm_partition(0)
        logger.info(f"Disarm all partitions: {result}")
        if result.get("success"):
            with cache_lock:
                if status_cache["data"] and "partitions" in status_cache["data"]:
                    for pid in status_cache["data"]["partitions"]:
                        status_cache["data"]["partitions"][pid]["armed"] = False
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error disarming all partitions: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/zone/<int:zone_id>/bypass", methods=["POST"])
def api_bypass_zone(zone_id):
    """Bypass a specific zone."""
    try:
        result = client.bypass_zone(zone_id)
        logger.info(f"Bypass zone {zone_id}: {result}")
        if result.get("success"):
            with cache_lock:
                if status_cache["data"] and "zones" in status_cache["data"]:
                    if zone_id in status_cache["data"]["zones"]:
                        status_cache["data"]["zones"][zone_id]["bypassed"] = True
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error bypassing zone {zone_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/zone/<int:zone_id>/unbypass", methods=["POST"])
def api_unbypass_zone(zone_id):
    """Remove bypass from a specific zone."""
    try:
        result = client.unbypass_zone(zone_id)
        logger.info(f"Unbypass zone {zone_id}: {result}")
        if result.get("success"):
            with cache_lock:
                if status_cache["data"] and "zones" in status_cache["data"]:
                    if zone_id in status_cache["data"]["zones"]:
                        status_cache["data"]["zones"][zone_id]["bypassed"] = False
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error unbypassing zone {zone_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/panic", methods=["POST"])
def api_panic():
    """Trigger panic alarm."""
    try:
        panic_type = request.json.get("type", 1) if request.json else 1
        result = client.trigger_panic(panic_type)
        logger.warning(f"PANIC triggered (type {panic_type}): {result}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error triggering panic: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/test")
def api_test():
    """Test connection to the alarm panel."""
    try:
        result = client.test_connection()
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/config")
def api_config():
    """Return current add-on configuration (non-sensitive)."""
    return jsonify({
        "host": AMT_HOST,
        "port": AMT_PORT,
        "updateInterval": UPDATE_INTERVAL,
    })


# ============================================================================
# Startup
# ============================================================================

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("AMT-8000 Alarm Manager Starting")
    logger.info(f"Host: {AMT_HOST}:{AMT_PORT}")
    logger.info(f"Update interval: {UPDATE_INTERVAL}s")
    logger.info(f"Ingress path: {INGRESS_PATH}")
    logger.info("=" * 60)

    # Start background status polling thread
    status_thread = threading.Thread(target=update_status_cache, daemon=True)
    status_thread.start()
    logger.info("Status polling thread started")

    # Start Flask server
    app.run(
        host="0.0.0.0",
        port=8199,
        debug=False,
        use_reloader=False,
    )
