import requests
import json
import time
from typing import Optional

SHELLY_EM_URL = "http://192.168.1.162/rpc"
SHELLY_SOCKET_BASE = "http://192.168.1.51/relay/0?turn="

# Configure how often to read & act (in seconds)
POLL_INTERVAL_SECONDS = 5  # ← change this to your desired loop interval

# Business rule threshold
INJECTION_THRESHOLD = -30.0  # act_power < -30 => injection into grid

# Optional: stop acting after too many consecutive failures (set to None to disable)
MAX_CONSECUTIVE_FAILURES = 10

# How many seconds to wait for HTTP operations before timing out
HTTP_TIMEOUT = 5


def socket_control(status: str) -> bool:
    """
    Control the relay with 'on' or 'off'.
    Returns True if the call appears successful (HTTP 200), otherwise False.
    """
    status = status.strip().lower()
    if status not in ("on", "off"):
        print(f"[socket_control] Invalid status '{status}'. Expected 'on' or 'off'.")
        return False

    url = SHELLY_SOCKET_BASE + status
    try:
        r = requests.get(url, timeout=HTTP_TIMEOUT)
        r.raise_for_status()
        print(f"[socket_control] Relay turned {status}.")
        return True
    except requests.exceptions.Timeout:
        print("[socket_control] Connectivity issue: Request timed out.")
    except requests.exceptions.ConnectionError:
        print("[socket_control] Connectivity issue: Unable to reach the relay.")
    except requests.exceptions.RequestException as e:
        print(f"[socket_control] Request error: {e}")
    return False


def read_meter() -> Optional[float]:
    """
    Query Shelly EM for active power.
    Return:
      - float value (e.g., -69.8) on success
      - None on connectivity / parsing errors
    """
    payload = {
        "id": "1",
        "method": "EM1.GetStatus",
        "params": {"id": "0"}
    }
    headers = {
        "Content-type": "application/json",
        "Accept": "application/json"
    }

    try:
        resp = requests.post(SHELLY_EM_URL, json=payload, headers=headers, timeout=HTTP_TIMEOUT)
        resp.raise_for_status()

        data = resp.json()
        result = data.get("result", {})
        act_power_value = result.get("act_power", None)

        if act_power_value is None:
            print("[read_meter] 'act_power' missing in response:", data)
            return None
        try:
            value = float(act_power_value)
        except (TypeError, ValueError):
            print(f"[read_meter] 'act_power' not numeric: {act_power_value!r}")
            return None

        print("Current Active Power:", value)
        return value

    except requests.exceptions.ConnectionError:
        print("[read_meter] Connectivity issue: Unable to reach the server.")
    except requests.exceptions.Timeout:
        print("[read_meter] Connectivity issue: Request timed out.")
    except requests.exceptions.JSONDecodeError as e:
        print(f"[read_meter] Invalid JSON response: {e}")
    except requests.exceptions.RequestException as e:
        print(f"[read_meter] Request error: {e}")

    return None


if __name__ == '__main__':
    print(f"Starting Shelly loop. Interval = {POLL_INTERVAL_SECONDS}s. Press Ctrl+C to stop.")
    consecutive_failures = 0

    try:
        while True:
            value = read_meter()

            if value is None:
                consecutive_failures += 1
                print(f"[main] Read failed (#{consecutive_failures}). "
                      f"Nu s-a putut citi puterea activă.")

                if MAX_CONSECUTIVE_FAILURES is not None and consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    print(f"[main] Reached {MAX_CONSECUTIVE_FAILURES} consecutive failures. "
                          "Not toggling relay to avoid unsafe behavior.")
                # Sleep then continue to next iteration
                time.sleep(POLL_INTERVAL_SECONDS)
                continue

            # reset failure counter on success
            consecutive_failures = 0

            # Decision logic
            if value < INJECTION_THRESHOLD:
                print("Atenție, energie injectată în rețea, pornire consumatori.")
                socket_control("on")
            else:
                print("Nivel consum în parametri, oprire consumatori.")
                socket_control("off")

            # Wait before next cycle
            time.sleep(POLL_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\n[main] Stopped by user. Exiting cleanly.")
