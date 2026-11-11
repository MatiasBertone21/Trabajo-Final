"""Block until Automation Lab services respond. Used by Jenkins pipelines."""
import sys
import time
import requests

SERVICES = {
    "backend": "http://localhost:8000/health",
    "vision-service": "http://localhost:8001/health",
    "react": "http://localhost:3000",
    "angular": "http://localhost:4200",
    "svelte": "http://localhost:5173",
}


def is_up(url: str, timeout_s: int = 60) -> bool:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            response = requests.get(url, timeout=3)
            if response.status_code < 500:
                return True
        except requests.RequestException:
            pass
        time.sleep(2)
    return False


def main() -> int:
    names = sys.argv[1:] or list(SERVICES.keys())
    down = []
    for name in names:
        url = SERVICES[name]
        ok = is_up(url, timeout_s=60)
        status = " OK " if ok else "DOWN"
        print(f"[{status}] {name:15s} -> {url}")
        if not ok:
            down.append(name)
    return 1 if down else 0


if __name__ == "__main__":
    sys.exit(main())

