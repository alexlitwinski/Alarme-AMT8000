"""
AMT-8000 iSEC2 Protocol Client
Adapted from the existing HACS integration example with additions
for zone bypass and enhanced status parsing.
"""

import socket
import struct
import logging
import threading
import time

logger = logging.getLogger(__name__)

TIMEOUT = 3  # Socket timeout in seconds

DST_ID = [0x00, 0x00]
OUR_ID = [0x8F, 0xFF]

COMMANDS = {
    "auth": [0xF0, 0xF0],
    "status": [0x0B, 0x4A],
    "arm_disarm": [0x40, 0x1E],
    "panic": [0x40, 0x1A],
    "bypass": [0x40, 0x1C],
}


def split_into_octets(n):
    """Split a 16-bit number into two octets."""
    if 0 <= n <= 0xFFFF:
        high_byte = (n >> 8) & 0xFF
        low_byte = n & 0xFF
        return [high_byte, low_byte]
    else:
        raise ValueError("Number out of range (0 to 65535)")


def calculate_checksum(buffer):
    """Calculate XOR checksum for a byte array."""
    checksum = 0
    for value in buffer:
        checksum ^= value
    checksum ^= 0xFF
    checksum &= 0xFF
    return checksum


def merge_octets(buf):
    """Merge two octets into a 16-bit integer."""
    return buf[0] * 256 + buf[1]


def battery_status_for(resp):
    """Retrieve the battery status string from payload byte."""
    batt = resp[134]
    statuses = {
        0x01: "dead",
        0x02: "low",
        0x03: "medium",
        0x04: "full",
    }
    return statuses.get(batt, "unknown")


def battery_percentage_for(resp):
    """Estimate battery percentage from status byte."""
    batt = resp[134]
    percentages = {
        0x01: 5,
        0x02: 25,
        0x03: 60,
        0x04: 100,
    }
    return percentages.get(batt, 0)


def get_system_status(payload):
    """Extract the overall system status from payload."""
    status = (payload[20] >> 5) & 0x03
    statuses = {
        0x00: "disarmed",
        0x01: "partial_armed",
        0x03: "armed_away",
    }
    return statuses.get(status, "unknown")


def build_status(data):
    """Build complete AMT-8000 status from raw byte response."""
    length = merge_octets(data[4:6]) - 2
    payload = data[8: 8 + length]

    if len(payload) < 143:
        raise ValueError(f"Invalid payload length: {len(payload)}, expected at least 143")

    model = "AMT-8000" if payload[0] == 1 else "Unknown"

    status = {
        "model": model,
        "version": f"{payload[1]}.{payload[2]}.{payload[3]}",
        "status": get_system_status(payload),
        "zonesFiring": (payload[20] & 0x08) > 0,
        "zonesClosed": (payload[20] & 0x04) > 0,
        "siren": (payload[20] & 0x02) > 0,
        "batteryStatus": battery_status_for(payload),
        "batteryPercentage": battery_percentage_for(payload),
        "tamper": (payload[71] & (1 << 0x01)) > 0,
        "zones": {},
        "partitions": {},
        "timestamp": time.time(),
    }

    # Initialize all 64 zones
    for i in range(64):
        zone_number = i + 1
        status["zones"][zone_number] = {
            "number": zone_number,
            "enabled": False,
            "open": False,
            "violated": False,
            "bypassed": False,
            "tamper": False,
            "lowBattery": False,
        }

    # Zones enabled (bytes 12-19, 8 bytes = 64 bits)
    for i, octet in enumerate(payload[12:20]):
        for j in range(8):
            zone_idx = j + i * 8
            if zone_idx < 64:
                status["zones"][zone_idx + 1]["enabled"] = (octet & (1 << j)) > 0

    # Zones open (bytes 38-45, 8 bytes)
    for i, octet in enumerate(payload[38:46]):
        for j in range(8):
            zone_idx = j + i * 8
            if zone_idx < 64:
                status["zones"][zone_idx + 1]["open"] = (octet & (1 << j)) > 0

    # Zones violated (bytes 46-53, 8 bytes)
    for i, octet in enumerate(payload[46:54]):
        for j in range(8):
            zone_idx = j + i * 8
            if zone_idx < 64:
                status["zones"][zone_idx + 1]["violated"] = (octet & (1 << j)) > 0

    # Zones bypassed/anulated (bytes 54-62, 8 bytes)
    for i, octet in enumerate(payload[54:62]):
        for j in range(8):
            zone_idx = j + i * 8
            if zone_idx < 64:
                status["zones"][zone_idx + 1]["bypassed"] = (octet & (1 << j)) > 0

    # Zone tamper (bytes 89-97, 8 bytes)
    for i, octet in enumerate(payload[89:97]):
        for j in range(8):
            zone_idx = j + i * 8
            if zone_idx < 64:
                status["zones"][zone_idx + 1]["tamper"] = (octet & (1 << j)) > 0

    # Zone low battery (bytes 105-113, 8 bytes)
    for i, octet in enumerate(payload[105:113]):
        for j in range(8):
            zone_idx = j + i * 8
            if zone_idx < 64:
                status["zones"][zone_idx + 1]["lowBattery"] = (octet & (1 << j)) > 0

    # Extract partition information (up to 16 partitions)
    max_partitions = min(16, len(payload) - 22)
    for i in range(max_partitions):
        if 22 + i >= len(payload):
            break
        octet = payload[22 + i]
        partition_number = i + 1
        status["partitions"][partition_number] = {
            "number": partition_number,
            "enabled": (octet & 0x80) > 0,
            "armed": (octet & 0x01) > 0,
            "firing": (octet & 0x04) > 0,
            "fired": (octet & 0x08) > 0,
            "stay": (octet & 0x40) > 0,
        }

    return status


class CommunicationError(Exception):
    """Exception raised for communication errors."""

    def __init__(self, message="Communication error"):
        self.message = message
        super().__init__(self.message)


class AuthError(Exception):
    """Exception raised for authentication errors."""

    def __init__(self, message="Authentication Error"):
        self.message = message
        super().__init__(self.message)


class AMT8000Client:
    """Thread-safe client for AMT-8000 alarm panel communication."""

    def __init__(self, host, port, password):
        self.host = host
        self.port = port
        self.password = password
        self.device_type = 1
        self.software_version = 0x10
        self._lock = threading.Lock()
        self._socket = None

    def _read_data(self):
        """Read data from socket, handling fragmented TCP packets."""
        header = self._socket.recv(6)
        if len(header) < 6:
            raise CommunicationError("Failed to read message header.")

        expected_len = struct.unpack("!H", header[4:6])[0]
        total_len = 8 + expected_len

        buffer = bytearray(header)

        bytes_to_read = total_len - len(buffer)
        while bytes_to_read > 0:
            packet = self._socket.recv(bytes_to_read)
            if not packet:
                raise CommunicationError("Connection broken while receiving data.")
            buffer.extend(packet)
            bytes_to_read -= len(packet)

        return buffer

    def _connect(self):
        """Create a new socket connection."""
        if self._socket is not None:
            self._close()

        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(TIMEOUT)
            self._socket.connect((self.host, self.port))
        except Exception as e:
            self._close()
            raise CommunicationError(f"Failed to connect to {self.host}:{self.port} - {e}")

    def _close(self):
        """Close socket connection."""
        if self._socket is None:
            return
        try:
            self._socket.settimeout(0.1)
        except Exception:
            pass
        try:
            self._socket.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        try:
            self._socket.close()
        except Exception:
            pass
        finally:
            self._socket = None

    def _auth(self):
        """Authenticate with the alarm panel."""
        if self._socket is None:
            raise CommunicationError("Client not connected.")

        pass_array = []
        for char in self.password:
            if len(self.password) != 6 or not char.isdigit():
                raise CommunicationError(
                    "Invalid password format. Must be exactly 6 digits."
                )
            pass_array.append(int(char))

        length = [0x00, 0x0A]
        data = (
            DST_ID
            + OUR_ID
            + length
            + COMMANDS["auth"]
            + [self.device_type]
            + pass_array
            + [self.software_version]
        )

        cs = calculate_checksum(data)
        payload = bytes(data + [cs])
        self._socket.send(payload)

        return_data = self._read_data()
        result = return_data[8:9][0]

        if result == 0:
            return True
        if result == 1:
            raise AuthError("Invalid password")
        if result == 2:
            raise AuthError("Incorrect software version")
        if result == 3:
            raise AuthError("Alarm panel will call back")
        if result == 4:
            raise AuthError("Waiting for user permission")
        raise CommunicationError("Unknown authentication response")

    def _execute_with_connection(self, func):
        """Execute a function with a fresh connection, using thread locking."""
        with self._lock:
            try:
                self._connect()
                self._auth()
                return func()
            except Exception:
                raise
            finally:
                self._close()

    def get_status(self):
        """Get the current status of the alarm panel."""

        def _status():
            length = [0x00, 0x02]
            status_data = DST_ID + OUR_ID + length + COMMANDS["status"]
            cs = calculate_checksum(status_data)
            payload = bytes(status_data + [cs])
            self._socket.send(payload)
            return_data = self._read_data()
            return build_status(return_data)

        return self._execute_with_connection(_status)

    def arm_partition(self, partition):
        """Arm a specific partition (1-16). Use 0 for all partitions."""

        def _arm():
            p = 0xFF if partition == 0 else partition
            length = [0x00, 0x04]
            arm_data = DST_ID + OUR_ID + length + COMMANDS["arm_disarm"] + [p, 0x01]
            cs = calculate_checksum(arm_data)
            payload = bytes(arm_data + [cs])
            self._socket.send(payload)
            return_data = self._read_data()
            if return_data[8] == 0x91:
                return {"success": True, "result": "armed"}
            return {"success": False, "result": "not_armed"}

        return self._execute_with_connection(_arm)

    def disarm_partition(self, partition):
        """Disarm a specific partition (1-16). Use 0 for all partitions."""

        def _disarm():
            p = 0xFF if partition == 0 else partition
            length = [0x00, 0x04]
            arm_data = DST_ID + OUR_ID + length + COMMANDS["arm_disarm"] + [p, 0x00]
            cs = calculate_checksum(arm_data)
            payload = bytes(arm_data + [cs])
            self._socket.send(payload)
            return_data = self._read_data()
            if return_data[8] == 0x91:
                return {"success": True, "result": "disarmed"}
            return {"success": False, "result": "not_disarmed"}

        return self._execute_with_connection(_disarm)

    def bypass_zone(self, zone_number):
        """Bypass (anulate) a specific zone."""

        def _bypass():
            length = [0x00, 0x04]
            bypass_data = DST_ID + OUR_ID + length + COMMANDS["bypass"] + [zone_number, 0x01]
            cs = calculate_checksum(bypass_data)
            payload = bytes(bypass_data + [cs])
            self._socket.send(payload)
            return_data = self._read_data()
            if return_data[8] == 0x91 or return_data[7] == 0xFE:
                return {"success": True, "result": "bypassed"}
            return {"success": False, "result": "not_bypassed"}

        return self._execute_with_connection(_bypass)

    def unbypass_zone(self, zone_number):
        """Remove bypass from a specific zone."""

        def _unbypass():
            length = [0x00, 0x04]
            bypass_data = DST_ID + OUR_ID + length + COMMANDS["bypass"] + [zone_number, 0x00]
            cs = calculate_checksum(bypass_data)
            payload = bytes(bypass_data + [cs])
            self._socket.send(payload)
            return_data = self._read_data()
            if return_data[8] == 0x91 or return_data[7] == 0xFE:
                return {"success": True, "result": "unbypass"}
            return {"success": False, "result": "not_unbypass"}

        return self._execute_with_connection(_unbypass)

    def trigger_panic(self, panic_type=1):
        """Trigger panic alarm. Type 1 = audible, 2 = silent."""

        def _panic():
            length = [0x00, 0x03]
            panic_data = DST_ID + OUR_ID + length + COMMANDS["panic"] + [panic_type]
            cs = calculate_checksum(panic_data)
            payload = bytes(panic_data + [cs])
            self._socket.send(payload)
            return_data = self._read_data()
            if return_data[7] == 0xFE:
                return {"success": True, "result": "triggered"}
            return {"success": False, "result": "not_triggered"}

        return self._execute_with_connection(_panic)

    def test_connection(self):
        """Test connection and return basic info."""
        try:
            status = self.get_status()
            return {
                "success": True,
                "model": status.get("model", "Unknown"),
                "version": status.get("version", "Unknown"),
                "battery": status.get("batteryStatus", "unknown"),
            }
        except AuthError as e:
            return {"success": False, "error": f"Authentication failed: {e.message}"}
        except CommunicationError as e:
            return {"success": False, "error": f"Connection failed: {e.message}"}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {str(e)}"}
