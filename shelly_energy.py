import requests
import json
from typing import Optional

SHELLY_EM_URL = "http://192.168.1.162/rpc"
SHELLY_SOCKET_BASE = "http://192.168.1.51/relay/0?turn="

# How many seconds to wait for a response before timing out
HTTP_TIMEOUT = 5

def socket_control(status: str) -> bool:
    """
    Control the relay with 'on' or 'off'.
    Returns True if the call appears successful (HTTP 200), otherwise False.
    """
    # Normalize and validate accepted values
    status = status.strip().lower()
    if status not in ("on", "off"):
        print(f"[socket_control] Invalid status '{status}'. Expected 'on' or 'off'.")
        return False

    url = SHELLY_SOCKET_BASE + status
    try:
        r = requests.get(url, timeout=HTTP_TIMEOUT)
        r.raise_for_status()
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
        # Using json=payload lets requests set headers/json correctly.
        resp = requests.post(SHELLY_EM_URL, json=payload, headers=headers, timeout=HTTP_TIMEOUT)
        resp.raise_for_status()

        # Parse JSON safely
        data = resp.json()
        # Expected schema: {"result": {"act_power": <number>, ...}, ...}
        result = data.get("result", {})
        act_power_value = result.get("act_power", None)

        if act_power_value is None:
            print("[read_meter] 'act_power' missing in response:", data)
            return None

        # Ensure it's numeric
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
    # Business rule: if act_power < -30 => injection into grid, turn consumers ON
    INJECTION_THRESHOLD = -30.0
    value = read_meter()

    if value is None:
        # Early return / safe handling if we couldn't read the meter
        print("Nu s-a putut citi puterea activă (probleme de conectivitate sau răspuns invalid).")
    else:
        if value < INJECTION_THRESHOLD:
            print("Atenție, energie injectată în rețea, pornire consumatori.")
            socket_control("on")
        else:
            print("Nivel consum în parametri, oprire consumatori.")
            socket_control("off")
